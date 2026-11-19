import { MAIN_PLUGINS } from "@html_editor/plugin_sets";
import { Plugin } from "@html_editor/plugin";
import { _t } from "@web/core/l10n/translation";
import { withSequence } from "@html_editor/utils/resource";

// T3503: the v18 editor lost the v14 image float options. Inline styles are
// used so that the layout is kept in emails as well as in PDF letters.
const MARGINS = { left: "0 18px 10px 0", right: "0 0 10px 18px", "": "" };

export class ImageFloatPlugin extends Plugin {
  static id = "imageFloat";
  static dependencies = ["history", "selection"];
  resources = {
    user_commands: [
      {
        id: "floatImageLeft",
        title: _t("Float left (text on the right)"),
        icon: "fa-align-left",
        run: () => this.floatImage("left"),
      },
      {
        id: "floatImageNone",
        title: _t("No text wrapping"),
        icon: "fa-align-justify",
        run: () => this.floatImage(""),
      },
      {
        id: "floatImageRight",
        title: _t("Float right (text on the left)"),
        icon: "fa-align-right",
        run: () => this.floatImage("right"),
      },
    ],
    toolbar_groups: [
      withSequence(27, { id: "image_float", namespace: "image" }),
    ],
    toolbar_items: [
      {
        id: "image_float_left",
        groupId: "image_float",
        commandId: "floatImageLeft",
        isActive: () => this.hasFloat("left"),
      },
      {
        id: "image_float_none",
        groupId: "image_float",
        commandId: "floatImageNone",
        isActive: () => this.hasFloat(""),
      },
      {
        id: "image_float_right",
        groupId: "image_float",
        commandId: "floatImageRight",
        isActive: () => this.hasFloat("right"),
      },
    ],
  };

  getTargetedImage() {
    return this.dependencies.selection
      .getTargetedNodes()
      .find((node) => node.tagName === "IMG");
  }

  hasFloat(side) {
    const img = this.getTargetedImage();
    return Boolean(img) && img.style.float === side;
  }

  floatImage(side) {
    const img = this.getTargetedImage();
    if (!img) {
      return;
    }
    img.classList.remove(
      "float-start",
      "float-end",
      "float-left",
      "float-right",
    );
    img.style.float = side;
    img.style.margin = MARGINS[side];
    this.dependencies.history.addStep();
  }
}

MAIN_PLUGINS.push(ImageFloatPlugin);
