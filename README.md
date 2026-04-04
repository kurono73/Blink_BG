## Overview
**Blink BG** allows you to instantly toggle background image opacity between values A and B, much like a blink. It is perfect for controlling background visibility during layout creation and modeling workflows.

---

## 🛠️ Core Features & Usage

### 1. Opacity Control
Manage your background opacity using two primary values and switch between them instantly.

* **Opacity A (Base):** The opacity of the background during normal workflow. *(Note: Unless manually adjusted by the user, this automatically fetches the actual current opacity of the background image.)*
* **Opacity B (Target):** The target opacity applied when the "Blink" action is triggered.
* **🔄 Swap Button (Refresh Icon):** Instantly swaps the values of Opacity A and Opacity B. Perfect for quick trial and error.

### 2. Blink Action (Visibility Toggle)
Control the background switching behavior to match your workflow. The default shortcut key is **`Alt + V`** *(This can be easily customized in Blender's Keymap preferences under the 3D View section)*.

* **🔓 Unlocked State (Hold & Delay Mode):**
  * **Shortcut (`Alt + V`):** The background switches to Opacity B **only while holding** the key, and instantly reverts to Opacity A upon release. Ideal for quick visual checks.
  * **UI Button Click:** Clicking the button switches to Opacity B, then automatically reverts to Opacity A after a specified delay (default is 0.3 seconds).You can change this in `Options`
* **🔒 Locked State (Toggle Mode):**
  * By clicking the lock icon (Closed Lock), both the shortcut and the UI button switch to a **Toggle behavior** (Press once to keep Opacity B, press again to return to Opacity A). Useful when you need to closely inspect the background for a longer duration.

### 3. 1-Click Depth Toggle
* **Depth: Front / Back:** A single click toggles the background image display between the front and back of your 3D models. The current state is indicated by the up/down arrow icon.

### Match Render Size
* **Match Render Size Button:** Located exclusively in the Camera Properties > Background Images panel. With one click, this automatically matches the scene's rendering resolution (Resolution X / Y) to the exact dimensions of your loaded image or movie clip.
* ***Note:** This feature specifically retrieves the resolution from the **first** background image added to the camera list. Subsequent images will not affect this calculation.*

---

## ⚙️ Advanced Options

### Target BG (Multi-Image Control)
If your camera has multiple background images set up (e.g., front view, side view), a **`Target BG`** index slider will automatically appear in the Blink BG panel. You can change this value to safely select which background image the add-on should control.

### Auto-Sync Pinned Camera
* **[Options] > Auto-Sync Pinned Camera:** In scenes with many cameras, it's common to "Pin" the Properties Editor. When this option is enabled, switching your Active Camera in the 3D viewport will **automatically sync the pinned Properties Editor** to display the newly selected camera's data, eliminating manual unpinning/repinning.
