# ⚡ BotManager v2

Painel web para **executar, monitorar e agendar scripts** localmente — sem precisar abrir terminal.  
Suporta **Python, Java, Node.js, Batch e Shell** com interface visual em tempo real.

---

## 📸 Funcionalidades

- ▶️ **Iniciar / Parar / Reiniciar** scripts com um clique
- 🖥️ **Logs em tempo real** com colorização por nível (erro, aviso, sucesso)
- ⏰ **Agendamento via Cron** (ex: todo dia às 09h)
- 🔍 **Detecção automática** da linguagem pela extensão do arquivo
- 📨 **Envio de input** para o stdin do processo em execução
- 📊 Contador de execuções e data do último início

---

## 🌐 Linguagens Suportadas

| Ícone | Linguagem | Extensão | Requisito |
|-------|-----------|----------|-----------|
| 🐍 | Python | `.py` | [Python](https://python.org) |
| ☕ | Java (compila + executa) | `.java` | [JDK](https://adoptium.net) |
| ☕ | Java JAR | `.jar` | [JRE/JDK](https://adoptium.net) |
| 🟩 | Node.js | `.js` | [Node.js](https://nodejs.org) |
| 🪟 | Batch | `.bat` / `.cmd` | Windows |
| 🐚 | Shell | `.sh` | Linux/macOS |

---

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/botmanager.git
cd botmanager
```

### 2. (Opcional) Crie um ambiente virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Inicie o servidor

```bash
python server.py
```

### 5. Acesse no navegador

```
http://localhost:8000
```

---

## 📁 Estrutura do Projeto

```
botmanager/
├── server.py        # Backend FastAPI
├── panel.html       # Painel visual (servido pelo backend)
├── requirements.txt # Dependências Python
├── .gitignore
└── README.md
```

---

## 📋 Como usar

### Adicionar um script

1. Clique em **+ Novo Script**
2. Preencha o nome e o **caminho completo** do arquivo:
   ```
   C:\Users\Usuario\Desktop\TicketMatheus\bot.py
   ```
3. Escolha a linguagem (ou deixe em **Auto**)
4. Opcionalmente adicione argumentos e/ou agendamento Cron
5. Clique em **Salvar**

### Agendamento Cron

| Expressão | Significado |
|-----------|-------------|
| `0 9 * * *` | Todo dia às 09:00 |
| `*/30 * * * *` | A cada 30 minutos |
| `0 8 * * 1` | Toda segunda-feira às 08:00 |
| `0 0 1 * *` | Todo dia 1º do mês à meia-noite |

---

## 🔧 Requisitos

- Python 3.8+
- pip

> Os runtimes (Java, Node.js, etc.) precisam estar instalados e disponíveis no **PATH** do sistema para que os respectivos scripts sejam executados.

---

## 📦 Dependências

```
fastapi
uvicorn
apscheduler
```

---

## 📄 Licença

MIT — sinta-se livre para usar, modificar e distribuir.
