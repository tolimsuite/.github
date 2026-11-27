<p align="center">
  <img src="https://github.com/tolimsuite.png?size=200" alt="TOLIM Technologies" width="120" height="120">
</p>

<h1 align="center">TOLIM Technologies</h1>

<p align="center">
  <strong>Cryptographic engineering, safely packaged.</strong><br>
  密码工程，安全交付。
</p>

<p align="center">
  We build fail-closed, policy-driven security infrastructure for the JVM.<br>
  我们为 JVM 构建失败关闭、策略驱动的安全基础设施。
</p>

<p align="center">
  <a href="https://tolim.cn">Website</a> ·
  <a href="https://github.com/tolimsuite/spissatus4j">spissatus4j</a> ·
  <a href="https://central.sonatype.com/artifact/cn.tolim.spissatus4j/spissatus4j-core">Maven Central</a>
</p>

<p align="center">
  <a href="#english">English</a> · <a href="#chinese">简体中文</a>
</p>

---

<a name="english"></a>
## English

### What we build

#### spissatus4j

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

### Get started

```groovy
dependencies {
    implementation 'cn.tolim.spissatus4j:spissatus4j-core:0.1.0'
}
```

Requires JDK 25. See the [repository](https://github.com/tolimsuite/spissatus4j) for the architecture, full module list and quick start.

---

<a name="chinese"></a>
## 简体中文

### 我们构建什么

#### spissatus4j

一个面向 Java 25 的密码工程库，把 JCA 与 Bouncy Castle 封装成稳定、策略驱动、失败关闭的 API。涵盖密钥、认证信封、Provider、国密算法以及可选的 Spring Boot 集成——不发明密码原语。

<p>
  <a href="https://github.com/tolimsuite/spissatus4j"><img alt="仓库" src="https://img.shields.io/badge/repository-spissatus4j-181717?logo=github"></a>
  <a href="https://central.sonatype.com/artifact/cn.tolim.spissatus4j/spissatus4j-core"><img alt="Maven Central" src="https://img.shields.io/maven-central/v/cn.tolim.spissatus4j/spissatus4j-core?label=Maven%20Central"></a>
  <a href="https://github.com/tolimsuite/spissatus4j/blob/main/LICENSE"><img alt="许可证" src="https://img.shields.io/badge/license-Apache--2.0-blue.svg"></a>
</p>

- **安全默认值** — AES-256-GCM、ChaCha20-Poly1305 与 SM4-GCM 是一等公民；默认拒绝 ECB、DES、RC4、MD5 与 SHA-1。
- **失败关闭** — 自检失败或运行时不变量被破坏时停止操作，而不是静默降级。
- **真实的密钥生命周期** — 状态机、用途隔离、轮换、保留、封装、导入/导出与销毁。
- **处处认证** — 非 AEAD 模式使用 Encrypt-then-MAC 包装；先验证，再解密。
- **稳定契约** — 应用依赖 `spissatus4j-contract`；Provider 可通过 SPI 替换。

**模块：** `contract` · `core` · `crypto` · `key` · `envelope` · `policy` · `bouncycastle` · `gm` · `spring-boot-starter`

### 快速开始

```groovy
dependencies {
    implementation 'cn.tolim.spissatus4j:spissatus4j-core:0.1.0'
}
```

需要 JDK 25。架构、完整模块列表与快速开始见[仓库](https://github.com/tolimsuite/spissatus4j)。

---

## Contributors · 贡献者

<p align="center">
  <a href="https://github.com/tolimsuite/spissatus4j/graphs/contributors">
    <img src="https://contrib.rocks/image?repo=tolimsuite/spissatus4j" alt="Contributors">
  </a>
</p>

---

<p align="center">
  <sub>© TOLIM Technologies Pte. Ltd. · Apache-2.0</sub>
</p>