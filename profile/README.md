<p align="center">
  <img src="https://github.com/tolimsuite.png?size=200" alt="TOLIM Technologies" width="120" height="120">
</p>

<h1 align="center">TOLIM Technologies</h1>

<p align="center">
  <strong>Cryptographic engineering, safely packaged.</strong>
</p>

<p align="center">
  We build fail-closed, policy-driven security infrastructure for the JVM.
</p>

<p align="center">
  <a href="https://tolim.cn">Website</a> ·
  <a href="https://github.com/tolimsuite/spissatus4j">spissatus4j</a> ·
  <a href="https://central.sonatype.com/artifact/cn.tolim.spissatus4j/spissatus4j-core">Maven Central</a>
</p>

---

## What we build

### spissatus4j

A Java 25 cryptographic engineering library that wraps JCA and Bouncy Castle into a stable, policy-driven, fail-closed API. Keys, authenticated envelopes, providers, GM/T algorithms and optional Spring Boot integration — without inventing primitives.

<p>
  <a href="https://github.com/tolimsuite/spissatus4j"><img alt="Repository" src="https://img.shields.io/badge/repository-spissatus4j-181717?logo=github"></a>
  <a href="https://central.sonatype.com/artifact/cn.tolim.spissatus4j/spissatus4j-core"><img alt="Maven Central" src="https://img.shields.io/maven-central/v/cn.tolim.spissatus4j/spissatus4j-core?label=Maven%20Central"></a>
  <a href="https://github.com/tolimsuite/spissatus4j/blob/main/LICENSE"><img alt="License: Apache-2.0" src="https://img.shields.io/badge/license-Apache--2.0-blue.svg"></a>
</p>

- **Safe defaults** — AES-256-GCM, ChaCha20-Poly1305 and SM4-GCM are first-class; ECB, DES, RC4, MD5 and SHA-1 are denied by default.
- **Fail-closed** — failed self-checks and broken runtime invariants stop operations instead of silently downgrading.
- **Real key lifecycle** — state machine, usage isolation, rotation, retention, wrapping, import/export and destruction.
- **Authenticated everywhere** — non-AEAD modes are wrapped with Encrypt-then-MAC; verification happens before decryption.
- **Stable contracts** — applications depend on `spissatus4j-contract`; providers are replaceable through SPI.

**Modules:** `contract` · `core` · `crypto` · `key` · `envelope` · `policy` · `bouncycastle` · `gm` · `spring-boot-starter`

## Get started

```groovy
dependencies {
    implementation 'cn.tolim.spissatus4j:spissatus4j-core:0.1.0'
}
```

Requires JDK 25. See the [repository](https://github.com/tolimsuite/spissatus4j) for the architecture, full module list and quick start.

---

<p align="center">
  <sub>© TOLIM Technologies Pte. Ltd. · Apache-2.0</sub>
</p>