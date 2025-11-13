#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod python_bridge;
mod commands;

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            commands::run_simulation
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[tauri::command]
fn run_simulation(params: String) -> String {
    // Call Python backend via Rust
    format!("Simulating with: {}", params)
}
