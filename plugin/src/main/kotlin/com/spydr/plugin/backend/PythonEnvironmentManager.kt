package com.spydr.plugin.backend

import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.progress.ProgressIndicator
import java.io.File
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import java.nio.file.StandardCopyOption
import java.util.concurrent.TimeUnit
import java.util.zip.ZipInputStream

/**
 * Auto-setup of the Python backend environment:
 *
 * 1. Extracts the bundled backend from plugin resources (`backend.zip`)
 *    to `~/.spydr/backend/`.
 * 2. Discovers a system Python 3 interpreter.
 * 3. Creates a virtual environment (`.venv`) inside the backend directory.
 * 4. Installs `requirements.txt` dependencies into the venv.
 *
 * The whole process is idempotent — repeated calls skip already-completed
 * steps.  The backend is only re-extracted when the plugin version changes
 * (the `.venv` is preserved across upgrades to avoid re-installing deps
 * every time).
 */
class PythonEnvironmentManager private constructor() {

    companion object {
        private val LOG = Logger.getInstance(PythonEnvironmentManager::class.java)

        private const val BACKEND_RESOURCE = "/backend.zip"
        private const val VERSION_FILE = ".plugin_version"

        private val IS_WINDOWS = System.getProperty("os.name").lowercase().contains("win")

        private val BASE_DIR: Path = Paths.get(System.getProperty("user.home"), ".spydr")
        val BACKEND_DIR: Path = BASE_DIR.resolve("backend")
        val VENV_DIR: Path = BACKEND_DIR.resolve(".venv")

        val VENV_PYTHON: Path
            get() = if (IS_WINDOWS) {
                VENV_DIR.resolve("Scripts").resolve("python.exe")
            } else {
                // Prefer python3, fall back to python (some Linux venvs
                // only create the unversioned symlink).
                val py3 = VENV_DIR.resolve("bin").resolve("python3")
                if (Files.exists(py3)) py3
                else VENV_DIR.resolve("bin").resolve("python")
            }

        val VENV_PIP: Path
            get() = if (IS_WINDOWS)
                VENV_DIR.resolve("Scripts").resolve("pip.exe")
            else
                VENV_DIR.resolve("bin").resolve("pip")

        @JvmStatic
        val instance = PythonEnvironmentManager()
    }

    /** Result of [ensureReady]. */
    data class SetupResult(
        val pythonPath: String,
        val workingDir: String,
        val success: Boolean,
        val errorMessage: String? = null,
    )

    // -------------------------------------------------------------------
    // Public API
    // -------------------------------------------------------------------

    /**
     * Ensure the backend is fully set up and ready to run.
     *
     * **Must be called from a background thread** — the method performs
     * potentially long I/O (extracting zip, creating venv, pip install).
     *
     * @param pluginVersion  current plugin version used for cache
     *                       invalidation (re-extract when it changes).
     * @param indicator      optional [ProgressIndicator] for user feedback.
     */
    fun ensureReady(
        pluginVersion: String,
        indicator: ProgressIndicator?,
    ): SetupResult {
        try {
            // Step 1: Extract backend sources from plugin JAR
            indicator?.text = "Извлечение бэкенда…"
            indicator?.fraction = 0.1
            extractBackendIfNeeded(pluginVersion)

            // Step 2: Create venv (if not present)
            indicator?.text = "Настройка Python окружения…"
            indicator?.fraction = 0.3
            ensureVenv(indicator)

            // Step 3: Install pip dependencies (if not installed)
            indicator?.text = "Проверка зависимостей…"
            indicator?.fraction = 0.5
            installDependenciesIfNeeded(indicator)

            indicator?.text = "Готово"
            indicator?.fraction = 1.0

            return SetupResult(
                pythonPath = VENV_PYTHON.toString(),
                workingDir = BACKEND_DIR.toString(),
                success = true,
            )
        } catch (e: Exception) {
            LOG.error("Environment setup failed", e)
            return SetupResult(
                pythonPath = "",
                workingDir = "",
                success = false,
                errorMessage = e.message ?: "Unknown error",
            )
        }
    }

    /**
     * Try to find a working Python 3 interpreter on the system.
     *
     * Checks common names (`python3`, `python`) and well-known absolute
     * paths (`/usr/local/bin/python3`, `/opt/homebrew/bin/python3`, …).
     *
     * @return absolute command/path to Python 3, or `null` if none found.
     */
    fun findSystemPython(): String? {
        val commands = if (IS_WINDOWS) listOf("python", "python3", "py")
                       else listOf("python3", "python")

        val absolutePaths = if (IS_WINDOWS) emptyList() else listOf(
            "/usr/local/bin/python3",
            "/usr/bin/python3",
            "/opt/homebrew/bin/python3",
        )

        for (cmd in commands) {
            if (isPython3(cmd)) return cmd
        }
        for (path in absolutePaths) {
            if (File(path).exists() && isPython3(path)) return path
        }
        return null
    }

    // -------------------------------------------------------------------
    // Step 1: Extract backend.zip
    // -------------------------------------------------------------------

    private fun extractBackendIfNeeded(pluginVersion: String) {
        val versionFile = BACKEND_DIR.resolve(VERSION_FILE)

        if (Files.exists(versionFile)) {
            val existing = Files.readString(versionFile).trim()
            if (existing == pluginVersion) {
                LOG.info("Backend already extracted (v$pluginVersion)")
                return
            }
        }

        LOG.info("Extracting backend to $BACKEND_DIR (v$pluginVersion)")

        // Clean everything except .venv (preserve installed packages)
        if (Files.exists(BACKEND_DIR)) {
            BACKEND_DIR.toFile().listFiles()?.forEach { f ->
                if (f.name != ".venv") f.deleteRecursively()
            }
        }

        Files.createDirectories(BACKEND_DIR)

        val stream = javaClass.getResourceAsStream(BACKEND_RESOURCE)
            ?: throw IllegalStateException(
                "Bundled backend resource not found: $BACKEND_RESOURCE"
            )

        ZipInputStream(stream).use { zis ->
            generateSequence { zis.nextEntry }.forEach { entry ->
                val target = BACKEND_DIR.resolve(entry.name)
                if (entry.isDirectory) {
                    Files.createDirectories(target)
                } else {
                    Files.createDirectories(target.parent)
                    Files.copy(zis, target, StandardCopyOption.REPLACE_EXISTING)
                }
                zis.closeEntry()
            }
        }

        Files.writeString(versionFile, pluginVersion)
        LOG.info("Backend extracted successfully")
    }

    // -------------------------------------------------------------------
    // Step 2: Create venv
    // -------------------------------------------------------------------

    private fun ensureVenv(indicator: ProgressIndicator?) {
        if (Files.exists(VENV_PYTHON)) {
            LOG.info("Venv already exists at $VENV_DIR")
            return
        }

        val systemPython = findSystemPython()
            ?: throw IllegalStateException(
                "Python 3 не найден в системе.\n" +
                "Установите Python 3.10+ и убедитесь, что он доступен в PATH.\n\n" +
                when {
                    IS_WINDOWS -> "Скачайте Python с https://www.python.org/downloads/"
                    System.getProperty("os.name").lowercase().contains("mac") ->
                        "Установите через Homebrew: brew install python3"
                    else ->
                        "Установите: sudo apt install python3 python3-venv  " +
                        "(или аналогичная команда для вашего дистрибутива)"
                }
            )

        indicator?.text = "Создание виртуального окружения…"
        LOG.info("Creating venv with $systemPython at $VENV_DIR")

        val result = exec(
            listOf(systemPython, "-m", "venv", VENV_DIR.toString()),
            BACKEND_DIR.toFile(),
            timeoutSec = 120,
        )

        if (result.exitCode != 0) {
            // On Debian/Ubuntu python3-venv is a separate package
            val isVenvMissing = result.stderr.contains("ensurepip") ||
                    result.stderr.contains("No module named venv")
            val hint = if (isVenvMissing)
                "\n\nНа Debian/Ubuntu установите пакет:\n  sudo apt install python3-venv"
            else ""

            throw IllegalStateException(
                "Не удалось создать venv (exit ${result.exitCode}):\n${result.stderr}$hint"
            )
        }

        LOG.info("Venv created at $VENV_DIR")
    }

    // -------------------------------------------------------------------
    // Step 3: Install dependencies
    // -------------------------------------------------------------------

    private fun installDependenciesIfNeeded(indicator: ProgressIndicator?) {
        val reqFile = BACKEND_DIR.resolve("requirements.txt")
        if (!Files.exists(reqFile)) {
            LOG.warn("requirements.txt not found at $reqFile, skipping install")
            return
        }

        // Quick smoke-test: if the main dependency is importable, skip install
        val check = exec(
            listOf(VENV_PYTHON.toString(), "-c", "import langchain; print('ok')"),
            BACKEND_DIR.toFile(),
            timeoutSec = 15,
        )
        if (check.exitCode == 0 && check.stdout.contains("ok")) {
            LOG.info("Dependencies already installed, skipping")
            return
        }

        indicator?.text = "Установка Python-зависимостей (может занять несколько минут)…"
        LOG.info("Installing dependencies from $reqFile")

        val result = exec(
            listOf(
                VENV_PIP.toString(), "install",
                "-r", reqFile.toString(),
                "--quiet",
            ),
            BACKEND_DIR.toFile(),
            timeoutSec = 600,  // 10 min — first install can be slow
        )

        if (result.exitCode != 0) {
            throw IllegalStateException(
                "Ошибка установки зависимостей (exit ${result.exitCode}):\n${result.stderr}"
            )
        }

        LOG.info("Dependencies installed successfully")
    }

    // -------------------------------------------------------------------
    // Helpers
    // -------------------------------------------------------------------

    private fun isPython3(cmd: String): Boolean {
        return try {
            val r = exec(
                listOf(cmd, "--version"),
                File(System.getProperty("user.home")),
                timeoutSec = 5,
            )
            r.exitCode == 0 && r.stdout.contains("Python 3")
        } catch (_: Exception) {
            false
        }
    }

    private data class ExecResult(
        val exitCode: Int,
        val stdout: String,
        val stderr: String,
    )

    private fun exec(
        command: List<String>,
        workDir: File,
        timeoutSec: Long,
    ): ExecResult {
        val pb = ProcessBuilder(command)
            .directory(workDir)
            .redirectErrorStream(false)

        val proc = pb.start()

        val stdout = proc.inputStream.bufferedReader().readText()
        val stderr = proc.errorStream.bufferedReader().readText()

        val finished = proc.waitFor(timeoutSec, TimeUnit.SECONDS)
        if (!finished) {
            proc.destroyForcibly()
            throw IllegalStateException(
                "Процесс не завершился за ${timeoutSec}с: ${command.joinToString(" ")}"
            )
        }

        return ExecResult(proc.exitValue(), stdout, stderr)
    }
}
