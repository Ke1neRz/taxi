CREATE DATABASE IF NOT EXISTS taxi;

CREATE TABLE IF NOT EXISTS taxi.users
(
    id UInt64,
    name String,
    second_name String,
    count_trips UInt32,
    rating Float32,
    phone_number String,
    gender LowCardinality(String),
    is_taxist UInt8,
    balance Float64
)
ENGINE = MergeTree
ORDER BY id;

CREATE TABLE IF NOT EXISTS taxi.trips
(
    id UInt64,
    user_id UInt64,
    taxist_id UInt64,
    tarif LowCardinality(String),
    weather LowCardinality(String),
    start_point String,
    end_point String,
    intermediate_point String,
    distance Float64,
    cost Float64,
    datetime_start DateTime64(3, 'UTC'),
    datetime_end DateTime64(3, 'UTC'),
    child_seat UInt8,
    pets UInt8,
    rating Float32,
    travel_time_seconds UInt32,
    taxist_count UInt32,
    is_anomaly UInt8
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(datetime_start)
ORDER BY (datetime_start, id);
