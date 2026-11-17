use eframe::egui;
use ratatui::{
    backend::CrosstermBackend,
    layout::{Constraint, Direction, Layout},
    style::{Color, Style},
    widgets::{Block, Borders, Paragraph},
    Terminal,
};
use std::{collections::HashMap, io, time::Duration};
use sysinfo::{ProcessRefreshKind, ProcessStatus, System};

// ============================================================================
// RING 1: CORE TELEMETRY ENGINE (Data & Process Acquisition + Mitigation)
// ============================================================================
struct TelemetryEngine {
    sys: System,
}

impl TelemetryEngine {
    fn new() -> Self {
        let mut sys = System::new_all();
        sys.refresh_all();
        Self { sys }
    }

    fn refresh(&mut self) {
        self.sys.refresh_processes_specifics(ProcessRefreshKind::new().with_cpu());
        // Automatically check and neutralize fork bombs on every telemetry cycle
        self.mitigate_fork_bomb();
    }

    /// Automatically detects a fork bomb spike and terminates related processes
    fn mitigate_fork_bomb(&mut self) {
        const FORK_THRESHOLD: usize = 800;
        let total_procs = self.sys.processes().len();

        if total_procs > FORK_THRESHOLD {
            // Count process name occurrences to find the fork bomb culprit
            let mut name_counts: HashMap<String, usize> = HashMap::new();
            for (_, p) in self.sys.processes() {
                let name = p.name().to_string();
                *name_counts.entry(name).or_insert(0) += 1;
            }

            // Find the most frequent process name exceeding a spawn burst count (>= 50 instances)
            if let Some((rogue_name, count)) = name_counts.into_iter().max_by_key(|&(_, c)| c) {
                if count >= 50 {
                    let my_pid = std::process::id();
                    eprintln!(
                        "\n[!] 🚨 CRITICAL: FORK BOMB DETECTED! ({} total procs). Purging {} instances of runaway process '{}'...",
                        total_procs, count, rogue_name
                    );

                    for (pid, p) in self.sys.processes() {
                        if p.name() == rogue_name {
                            let pid_u32 = pid.as_u32();
                            // Protect critical system processes (PID <= 1) and our own monitor
                            if pid_u32 != my_pid && pid_u32 > 1 {
                                p.kill();
                            }
                        }
                    }
                }
            }
        }
    }

    fn get_total_processes(&self) -> usize {
        self.sys.processes().len()
    }

    fn analyze_processes(&self) -> (f32, usize, Vec<(u32, String, f32)>) {
        let mut duet_cpu = 0.0;
        let mut zombie_count = 0;
        let mut procs: Vec<(u32, String, f32)> = Vec::new();

        for (pid, p) in self.sys.processes() {
            let name = p.name().to_string();
            let cpu = p.cpu_usage();

            if p.status() == ProcessStatus::Zombie {
                zombie_count += 1;
            }
            if name.contains("duetexpertd") {
                duet_cpu = cpu;
            }
            procs.push(((*pid).as_u32(), name, cpu));
        }

        // Sort numerically by PID (Process ID) ascending
        procs.sort_by(|a, b| a.0.cmp(&b.0));
        
        (duet_cpu, zombie_count, procs)
    }
}

// ============================================================================
// RING 2: SECURITY & DEFENSE LAYER (Zombie & Fork-Bomb Protection)
// ============================================================================
struct SecurityGuard;

impl SecurityGuard {
    fn evaluate_security(zombie_count: usize, total_procs: usize) -> (String, Color, egui::Color32) {
        const FORK_THRESHOLD: usize = 800;

        if total_procs > FORK_THRESHOLD {
            (
                format!(" [!] CRITICAL: FORK BOMB MITIGATED ({} procs - Rogue processes terminated!) ", total_procs),
                Color::Red,
                egui::Color32::RED,
            )
        } else if zombie_count > 0 {
            (
                format!(" [!] WARNING: {} ZOMBIE PROCESSES DETECTED! ", zombie_count),
                Color::Red,
                egui::Color32::LIGHT_RED,
            )
        } else {
            (
                " Status: Secure [Fork Bomb Guard & Zero Zombies Active] ".to_string(),
                Color::Green,
                egui::Color32::GREEN,
            )
        }
    }
}

// ============================================================================
// RING 3: INTERFACE / PRESENTATION LAYER (TUI & GUI Routing)
// ============================================================================
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();

    // Outer Layer: Graphical Desktop Window (GUI)
    if args.iter().any(|arg| arg == "--gui") {
        let options = eframe::NativeOptions {
            viewport: egui::ViewportBuilder::default().with_inner_size([550.0, 650.0]),
            ..Default::default()
        };
        return eframe::run_native(
            "Mesh System & Security Monitor",
            options,
            Box::new(|_| Ok(Box::new(GuiApp::default()))),
        )
        .map_err(|e| e.into());
    }

    // Outer Layer: Terminal UI (TUI) with Scroll Support
    run_tui()
}

// --- TUI Implementation with Scroll Support ---
fn run_tui() -> Result<(), Box<dyn std::error::Error>> {
    crossterm::terminal::enable_raw_mode()?;
    let mut stdout = io::stdout();
    crossterm::execute!(stdout, crossterm::terminal::EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let mut engine = TelemetryEngine::new();
    let mut scroll_offset: usize = 0;

    loop {
        engine.refresh();
        let total_procs = engine.get_total_processes();
        let (duet_cpu, zombie_count, procs) = engine.analyze_processes();

        let (sec_msg, tui_color, _) = SecurityGuard::evaluate_security(zombie_count, total_procs);

        terminal.draw(|f| {
            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([
                    Constraint::Length(3),
                    Constraint::Length(3),
                    Constraint::Min(10),
                ])
                .split(f.size());

            // 1. Health Header
            let header = Paragraph::new(format!(" Processes: {} | Duet CPU: {:.1}% ", total_procs, duet_cpu))
                .style(Style::default().fg(Color::Cyan))
                .block(Block::default().borders(Borders::ALL).title(" System Telemetry "));
            f.render_widget(header, chunks[0]);

            // 2. Security Guard Status
            let status = Paragraph::new(sec_msg)
                .style(Style::default().fg(tui_color))
                .block(Block::default().borders(Borders::ALL).title(" Security Ring "));
            f.render_widget(status, chunks[1]);

            // 3. Scrollable All Processes View (Sorted by PID)
            let max_visible_rows = chunks[2].height.saturating_sub(2) as usize;
            if scroll_offset > procs.len().saturating_sub(max_visible_rows) {
                scroll_offset = procs.len().saturating_sub(max_visible_rows);
            }

            let visible_procs: String = procs
                .iter()
                .skip(scroll_offset)
                .take(max_visible_rows)
                .map(|(pid, name, cpu)| format!(" PID {:<6} | {:<28} | {:>5.1}%\n", pid, name, cpu))
                .collect();

            let title_str = format!(" All Processes (Sorted by PID | Showing {}-{} of {}) [Up/Down or j/k to Scroll, q to Quit] ", 
                scroll_offset + 1, 
                (scroll_offset + max_visible_rows).min(procs.len()), 
                procs.len()
            );

            let proc_widget = Paragraph::new(visible_procs)
                .block(Block::default().borders(Borders::ALL).title(title_str));
            f.render_widget(proc_widget, chunks[2]);
        })?;

        // Handle keyboard input for scrolling and exiting
        if crossterm::event::poll(Duration::from_millis(100))? {
            if let crossterm::event::Event::Key(key) = crossterm::event::read()? {
                match key.code {
                    crossterm::event::KeyCode::Char('q') => break,
                    crossterm::event::KeyCode::Down | crossterm::event::KeyCode::Char('j') => {
                        scroll_offset = scroll_offset.saturating_add(1);
                    }
                    crossterm::event::KeyCode::Up | crossterm::event::KeyCode::Char('k') => {
                        scroll_offset = scroll_offset.saturating_sub(1);
                    }
                    crossterm::event::KeyCode::PageDown => {
                        scroll_offset = scroll_offset.saturating_add(10);
                    }
                    crossterm::event::KeyCode::PageUp => {
                        scroll_offset = scroll_offset.saturating_sub(10);
                    }
                    _ => {}
                }
            }
        }
    }

    crossterm::terminal::disable_raw_mode()?;
    crossterm::execute!(terminal.backend_mut(), crossterm::terminal::LeaveAlternateScreen)?;
    Ok(())
}

// --- GUI Implementation ---
struct GuiApp {
    engine: TelemetryEngine,
}

impl Default for GuiApp {
    fn default() -> Self {
        Self { engine: TelemetryEngine::new() }
    }
}

impl eframe::App for GuiApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        self.engine.refresh();
        let total_procs = self.engine.get_total_processes();
        let (_, zombie_count, procs) = self.engine.analyze_processes();
        let (_, _, gui_color) = SecurityGuard::evaluate_security(zombie_count, total_procs);

        egui::CentralPanel::default().show(ctx, |ui| {
            ui.heading("🛡️ Mesh Security & Telemetry Monitor (Sorted by PID)");
            ui.separator();

            ui.horizontal(|ui| {
                ui.label(format!("Total Processes: {}", total_procs));
                if zombie_count > 0 {
                    ui.colored_label(egui::Color32::RED, format!("⚠️ Zombies: {}", zombie_count));
                } else {
                    ui.colored_label(gui_color, "🛡️ System Clean");
                }
            });

            ui.add_space(8.0);
            ui.label("All Active Processes (PID Scroll):");

            // Full scrollable view containing every process sorted by PID
            egui::ScrollArea::vertical().max_height(450.0).show(ui, |ui| {
                for (pid, name, cpu) in &procs {
                    ui.horizontal(|ui| {
                        ui.label(format!("[{:<6}] {:<28}", pid, name));
                        ui.colored_label(egui::Color32::LIGHT_BLUE, format!("{:.1}%", cpu));
                    });
                }
            });
        });

        ctx.request_repaint();
    }
}
