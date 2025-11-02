use pyo3::prelude::*;
use tauri::command;

#[command]
fn run_simulation(params: String) -> Result<String, String> {
    Python::with_gil(|py| {
        let sys = PyModule::import(py, "sys")?;
        let polylog_module = PyModule::import(py, "polylog_core")?;
        polylog_module.call_method1("simulate", (params,))?
            .extract()?
            .map_err(|e: PyErr| e.to_string())
    })
}
