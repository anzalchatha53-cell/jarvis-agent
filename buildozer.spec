[app]
title = Jarvis Agent
package.name = jarvisagent
package.domain = org.jarvis

# (str) Source directory where the application files are located
source.dir = .

source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Automatically accept Android SDK license
android.accept_sdk_license = True
