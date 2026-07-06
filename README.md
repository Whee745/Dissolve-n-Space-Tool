# Dissolve & Space Tool

A Blender add-on that reduces a vertex selection to a user-defined count via iterative Limited Dissolve, then redistributes the remaining vertices evenly along the original curve using [LoopTools](https://extensions.blender.org/add-ons/looptools/) Space

Built to fit my own workflow. Working with dense edge loops often means manually dissolving vertices one by one until the shape looks right. It was slow and repetitive, so I vibecoded this to automate it. No formal coding background, but I studied every part of the code carefully to keep it clean and purposeful. Publishing it in case anyone else finds it useful. Feedback and contributions are welcome.

<img width="1920" height="1080" alt="Slide 16_9 - 1" src="https://github.com/user-attachments/assets/c15e0c88-3c35-4dab-9124-3dfe5d79552a" />

---

## What it does

1. **Dissolve** — finds the minimum dissolve angle needed to bring your selected vertex count down to a target number, using an exponential scan + binary search approach (~18 operations vs. hundreds for a brute-force method).
2. **Space** — runs LoopTools Space on the result to redistribute the remaining vertices evenly, preserving the overall curve shape.

Both steps can be run together with a single **Solve n Space** button, or independently.

---

## Requirements

- Blender **4.2 or later**
- The **[LoopTools](https://extensions.blender.org/add-ons/looptools/)** add-on must be installed as the **Space** step in this add-on relies on it to work correctly.

---

## Installation

**1. Enable [LoopTools](https://extensions.blender.org/add-ons/looptools/)** (if not already on)

Go to `Edit > Preferences > Add-ons`, search for **LoopTools**, and check the box to enable it.

**2. Install Dissolve & Space Tool**

- Download the latest `.zip` from the [Releases](../../releases) page
- In Blender, go to `Edit > Preferences > Add-ons`
- Click the dropdown arrow in the top-right corner and choose **Install from Disk**
- Select the downloaded `.zip` file
- Enable the add-on by checking the box next to **Dissolve & Space Tool**

---

## Where to find it

Switch to **Edit Mode** on any mesh object -> **Sidebar** -> **Edit** tab -> **Dissolve & Space Tool**.

---

## How to use

1. In Edit Mode, select the vertices you want to reduce
2. Set the **Target Verts** number — how many vertices you want left after dissolving
3. Click one of the three buttons:

| Button | What it does |
|---|---|
| **Solve n Space** | Runs Dissolve then Space back to back |
| **Dissolve** | Reduces vertex count to the target only |
| **Space** | Evenly redistributes the current selection only |

If the target count cannot be reached (e.g. the selection is too simple to dissolve further), a warning will appear in the status bar at the bottom of the Blender window.

---

## Credits

The **Space** step in this add-on relies on [LoopTools](https://extensions.blender.org/add-ons/looptools/), an amazing add-on.

- **Bart Crouch** — original author of LoopTools
- **Vladimir Spivak (cwolf3d)** — current maintainer of LoopTools

---

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE) for details.

---
