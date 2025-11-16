use tauri::command;

use crate::python_bridge::call_python_module;

#[command]
pub fn run_simulation(params: String) -> Result<String, String> {
    call_python_module("polylog_core", "simulate", &params).map_err(|e| e.to_string())
}

#[command]
pub fn get_unicode_symbols(params: String) -> Result<String, String> {
    call_python_module("polylog_core", "get_unicode_symbols", &params)
        .map_err(|e| e.to_string())
}

#[command]
pub fn launch_polyform(params: String) -> Result<String, String> {
    call_python_module("polylog_core", "launch_polyform", &params)
        .map_err(|e| e.to_string())
}
