// SPDX-License-Identifier: 0BSD
//! A Rust std program as a STELA port: threads, a channel, files, time.

use std::sync::mpsc;

fn main() {
    let name = std::env::args().nth(1).unwrap_or_else(|| String::from("world"));
    println!("rust-hello: hello, {name}");
    let (tx, rx) = mpsc::channel();
    let handles: Vec<_> = (0..4u64)
        .map(|i| {
            let tx = tx.clone();
            std::thread::spawn(move || tx.send(i * 10).unwrap())
        })
        .collect();
    drop(tx);
    for h in handles {
        h.join().unwrap();
    }
    let sum: u64 = rx.iter().sum();
    println!("rust-hello: threads sent {sum}");
    std::fs::write("/tmp/rust-hello.txt", b"rust").unwrap();
    let back = std::fs::read_to_string("/tmp/rust-hello.txt").unwrap();
    println!("rust-hello: file says {back}");
}
