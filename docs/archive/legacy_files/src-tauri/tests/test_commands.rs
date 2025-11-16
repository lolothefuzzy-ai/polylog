use polylog6_desktop::commands::run_simulation;

#[test]
fn test_run_simulation_ok() {
    let result = run_simulation("test_params".to_string());
    assert!(result.is_ok());
}

#[test]
fn test_run_simulation_err() {
    let result = run_simulation("invalid_params".to_string());
    assert!(result.is_err());
}
