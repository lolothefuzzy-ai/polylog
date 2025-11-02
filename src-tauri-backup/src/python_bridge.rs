use pyo3::prelude::*;

#[tauri::command]
fn run_simulation(params: String) -> Result<String, String> {
    Python::with_gil(|py| {
        let polylog = PyModule::import(py, "polylog_core")?;
        polylog.call_method1("simulate", (params,))?
            .extract()
            .map_err(|e| e.to_string())
    })
}
