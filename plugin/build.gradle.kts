plugins {
    id("java")
    id("org.jetbrains.kotlin.jvm") version "1.9.25"
    id("org.jetbrains.intellij") version "1.17.4"
}

group = "com.spydr.plugin"
version = "1.0.0"

repositories {
    mavenCentral()
}

dependencies {
    implementation("com.google.code.gson:gson:2.11.0")
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

intellij {
    version.set("2024.1.7")
    type.set("IC")
    plugins.set(listOf())
    instrumentCode.set(false)
}

// -------------------------------------------------------------------
// Bundle the Python backend as backend.zip inside the plugin JAR.
//
// At runtime PythonEnvironmentManager extracts this zip to
// ~/.spydr/backend/, creates a venv there, and installs dependencies
// automatically — the user never has to touch Python manually.
// -------------------------------------------------------------------

val zipBackend by tasks.registering(Zip::class) {
    group = "build"
    description = "Zip the Python backend sources for bundling into the plugin."

    from("../src") {
        into("src")
        exclude("**/__pycache__/**", "**/*.pyc")
    }
    from("../requirements.txt")
    from("../RULES.md")
    from("../docs") {
        into("docs")
    }

    archiveFileName.set("backend.zip")
    destinationDirectory.set(layout.buildDirectory.dir("generated-resources"))
}

sourceSets {
    main {
        resources.srcDir(layout.buildDirectory.dir("generated-resources"))
    }
}

tasks.named("processResources") {
    dependsOn(zipBackend)
}

// -------------------------------------------------------------------

tasks {
    withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile> {
        kotlinOptions.jvmTarget = "17"
    }

    patchPluginXml {
        sinceBuild.set("241")
        untilBuild.set("261.*")
    }

    buildSearchableOptions {
        enabled = false
    }
}
