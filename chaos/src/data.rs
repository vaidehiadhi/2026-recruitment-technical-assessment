use axum::{http::StatusCode, response::IntoResponse, Json};
use serde::{Deserialize, Serialize};
use serde_json::Value;

pub async fn process_data(Json(request): Json<DataRequest>) -> impl IntoResponse {
    let mut string_len = 0usize;
    let mut int_sum = 0i64;

    for value in request.data {
        if let Some(s) = value.as_str() {
            string_len += s.chars().count();
        } else if let Some(n) = value.as_i64() {
            int_sum += n;
        }
    }

    let response = DataResponse {
        string_len,
        int_sum,
    };

    (StatusCode::OK, Json(response))
}

#[derive(Deserialize)]
pub struct DataRequest {
    pub data: Vec<Value>,
}

#[derive(Serialize)]
pub struct DataResponse {
    pub string_len: usize,
    pub int_sum: i64,
}
