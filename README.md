# PyNexe

**Python to Windows executable builder using Nuitka**

PyNexe simplifies the process of creating standalone Windows executables from Python scripts. It wraps Nuitka's powerful translation and compilation capabilities with a clean YAML configuration system and rich CLI interface, making executable generation accessible and consistent.

## 🚀 Features

- **Wraps Nuitka's translation** - Converts Python to native C++ via Nuitka
- **YAML-based configuration** eliminates complex command-line arguments
- **Isolated build environments** ensure consistent and reproducible builds
- **Windows metadata support** for professional executable properties
- **UPX compression** reduces executable size automatically
- **Rich CLI interface** with detailed progress tracking, file validation, and clear error messages
- **Source code protection** through Nuitka's translation and obfuscation
- **Fast startup times** compared to interpreted Python scripts

## 📋 Requirements

- **Python 3.13+**
- **Windows 10/11** (64-bit)
- **Nuitka** (installed automatically)
- **Visual Studio Build Tools** (for Nuitka's C++ compilation)

## 📦 Installation

1. **Clone the repository:**
```bash
git clone https://github.com/kodezy/pynexe.git
cd pynexe
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Verify installation:**
```bash
python pynexe.py help
```

## ⚙️ Configuration

Create a `config.yaml` file in your project root:

```yaml
# Required settings
project_name: "my_app"
main_file: "main.py"
output_name: "my_app.exe"

# Optional settings
project_libs:
  - "requests"
  - "pandas"

include_packages:
  - "src"

include_data_dirs:
  - "assets=assets"

icon_file: "icon.ico"

windows_metadata:
  product_name: "My Application"
  file_description: "My Python Application"
  product_version: "1.0.0.0"
  file_version: "1.0.0.0"
  copyright: "My Company"
  company_name: "My Company"

# Advanced settings
build_libs:
  - "nuitka"        # Python to C++
  - "ordered-set"   # Dependency for Nuitka

nuitka_plugins:
  - "upx"           # Compress size
  - "no-qt"         # Exclude Qt
  - "tk-inter"      # Include Tkinter

nuitka_extra_args:
  - "--lto=no"      # Disable link-time optimization
  - "--show-scons"  # Show SCons build output
  - "--jobs=1"      # Single compilation job

cleanup_items:
  - "build"         # Remove build directory
  - "dist"          # Remove dist directory
```

## 🧪 Usage

### Basic Usage

1. **Create your Python script:**
```python
# main.py
import requests

def main():
    response = requests.get("https://api.github.com")
    print(f"Status: {response.status_code}")

if __name__ == "__main__":
    main()
```

2. **Build the executable:**
```bash
python pynexe.py run
```

3. **Result:** `my_app.exe` ready for distribution

### Advanced Usage

```bash
# Build with custom config
python pynexe.py run --config production.yaml

# Check project settings and file status
python pynexe.py info

# Show help
python pynexe.py help
```

## 🧠 How It Works

1. **Validation** - Checks that all required files exist before building
2. **Environment Setup** - Creates isolated build environment
3. **Dependency Resolution** - Installs required packages with progress feedback
4. **Nuitka Processing** - Nuitka translates and compiles Python to executable
5. **Optimization** - Applies UPX compression and metadata
6. **Cleanup** - Removes temporary build files
7. **Delivery** - Produces standalone executable with size information

## 🔒 Security Considerations

### Antivirus Warnings

Generated executables may trigger antivirus alerts. This is normal behavior:

**Common causes:**
- Nuitka-generated executables are flagged as suspicious
- UPX compression triggers heuristic detection
- New/uncommon executables treated as potential threats

**Solutions:**
- Add executable to antivirus whitelist
- Submit false positive report to antivirus vendor
- Use digital signature for commercial distribution
- Test thoroughly before distribution

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| Missing dependencies | Add to `project_libs` in config.yaml |
| Large executable size | UPX compression is enabled by default |
| Build errors | Check Python syntax and dependencies. The CLI now shows detailed error messages with suggestions |
| File not found errors | Use `python pynexe.py info` to check file status before building |
| Antivirus alerts | Add to whitelist or submit for analysis |
| Nuitka build fails | Ensure Visual Studio Build Tools installed |
| Config file not found | Create `config.yaml` in project root |
