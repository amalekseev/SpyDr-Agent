package com.spydr.plugin.settings

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.PersistentStateComponent
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage

/**
 * Persistent application-level settings for the SpyDR plugin.
 */
@State(
    name = "com.spydr.plugin.settings.SpydrSettingsState",
    storages = [Storage("SpydrPlugin.xml")]
)
class SpydrSettingsState : PersistentStateComponent<SpydrSettingsState.State> {

    data class State(
        /**
         * Path to the Python interpreter.
         * Empty → auto mode: the plugin creates its own venv inside
         * `~/.spydr/backend/.venv` and uses that.
         */
        var pythonPath: String = "",

        /** Default directory for generated .feature files. */
        var defaultFeatureDir: String = "",

        /**
         * Path to a `.env` file with API keys (GIGACHAT_*, etc.).
         * When set, the plugin passes it to the Python process via
         * the `SPYDR_DOTENV_PATH` environment variable.
         */
        var envFilePath: String = "",
    )

    private var myState = State()

    override fun getState(): State = myState

    override fun loadState(state: State) {
        myState = state
    }

    var pythonPath: String
        get() = myState.pythonPath
        set(value) { myState.pythonPath = value }

    var defaultFeatureDir: String
        get() = myState.defaultFeatureDir
        set(value) { myState.defaultFeatureDir = value }

    var envFilePath: String
        get() = myState.envFilePath
        set(value) { myState.envFilePath = value }

    /** `true` when the user has **not** overridden the Python path (bundled/auto mode). */
    val isAutoMode: Boolean
        get() = myState.pythonPath.isBlank()

    companion object {
        fun getInstance(): SpydrSettingsState {
            return ApplicationManager.getApplication().getService(SpydrSettingsState::class.java)
        }
    }
}
