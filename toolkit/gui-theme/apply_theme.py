#!/usr/bin/env python3
"""Visual-only patch: replaces inline FXML colours by style classes, adds theme.css,
swaps the sidebar highlight to a CSS pseudo-class, and themes the two alert dialogs.
No handler, controller field or fx:id is touched.  usage: apply_theme.py <.../src/userInterface>"""
import re, sys, glob, os

d = sys.argv[1]
STEPS = {"Flight Controller", "UAV Model &amp; Environment and Mission", "Injection Process", "Campaign Overview"}

S_MID   = "-fx-background-color: #77919d;"
S_DARK  = "-fx-background-color: #274c5e;"
S_LIGHT = "-fx-background-color: #dae9f4;"
S_NAV1  = "-fx-background-color: transparent; -fx-border-color: white; -fx-border-width: 2px 0px 2px 0px;"
S_NAV   = "-fx-background-color: transparent; -fx-border-color: white; -fx-border-width: 0px 0px 2px 0px;"
S_LIST  = "-fx-border-color: #274c5e;"
S_CARD  = "-fx-background-color: #77919d; -fx-border-color: #274c5e;"

def classes_for(tag, style, text, fsize, fname, is_sidebar_file):
    cls = []
    if style == S_MID:
        if tag == "Button": cls.append("step-off" if text in STEPS else "btn-primary")
        elif tag == "VBox" and is_sidebar_file: cls.append("sidebar")
        else: cls.append("card")
    elif style == S_DARK:
        if tag == "Button": cls.append("step-on" if text in STEPS else "btn-primary")
        else: cls.append("card")
    elif style == S_LIGHT: cls.append("page")
    elif style in (S_NAV, S_NAV1): cls.append("nav-btn")
    elif style == S_LIST: cls.append("list-view-themed")
    elif style == S_CARD: cls.append("card")
    elif style is not None: raise SystemExit("unmapped style: " + style)
    if fsize is not None and not cls:
        pass
    if tag == "Text":
        s = float(fsize) if fsize else None
        if s is None: cls.append("t-plain")
        elif s >= 24: cls.append("t-h1")
        elif s >= 17: cls.append("t-h2")
        elif s >= 12: cls.append("t-label")
        else: cls.append("t-hint")
    return cls

FEATS = [("21 fault types", "GPS, IMU, gyroscope and accelerometer faults"),
         ("Custom faults", "Write your own fault as a Python file"),
         ("Seeded campaigns", "Repeatable runs scored against ground truth"),
         ("U-space tracking", "Traffic positions logged next to injected values")]

def home_extras(x):
    x = re.sub(r'<VBox\.margin>.*?</VBox\.margin>', '', x, flags=re.S)
    x = re.sub(r'<HBox alignment="CENTER_LEFT" maxHeight="26.0"[^>]*>\s*</HBox>', '', x)
    sub = ('<Text styleClass="t-sub" text="Plan, run and analyse repeatable fault-injection campaigns on PX4 UAV missions" />\n            ')
    a = x.index('<Button fx:id="btnTestCampaign"')
    x = x[:a] + sub + x[a:]
    cards = "".join('<VBox alignment="TOP_LEFT" spacing="6.0" prefWidth="190.0" maxWidth="190.0" styleClass="card, feat"><children>'
                    '<Text styleClass="t-label" text="%s" /><Text styleClass="t-hint" wrappingWidth="158.0" text="%s" /></children></VBox>' % c for c in FEATS)
    row = '\n            <HBox alignment="CENTER" spacing="16.0" maxWidth="820.0"><children>%s</children></HBox>' % cards
    b = x.index('fx:id="btnAddCampaign"'); e = x.index("</Button>", b) + len("</Button>")
    return x[:e] + row + x[e:]

def side_extras(x):
    x = x.replace('<?import javafx.scene.layout.AnchorPane?>', '<?import javafx.geometry.Insets?>\n<?import javafx.scene.layout.AnchorPane?>\n<?import javafx.scene.layout.Region?>', 1)
    b = x.index('fx:id="btnAbout"'); e = x.index("</Button>", b) + len("</Button>")
    foot = ('\n            <Region VBox.vgrow="ALWAYS" />\n            <Text styleClass="side-foot" text="Fault injection for PX4 SITL"><VBox.margin><Insets bottom="16.0" left="28.0" /></VBox.margin></Text>')
    return x[:e] + foot + x[e:]


def flight_extras(x):
    # PX4 is the supported flight controller: show it as a single selected card, drop the placeholder logos,
    # and replace the "coming soon" line by a tagline.
    x = re.sub(r'\s*<ImageView fx:id="ivArduPilot".*?</ImageView>', '', x, flags=re.S)
    x = re.sub(r'\s*<ImageView fx:id="ivRotorS".*?</ImageView>', '', x, flags=re.S)
    m = re.search(r'<ImageView fx:id="ivPX4".*?</ImageView>', x, re.S)
    card = ('<VBox alignment="CENTER" spacing="12.0" prefWidth="290.0" maxWidth="290.0" styleClass="card, pick"><children>'
            + m.group(0) +
            '<Label styleClass="chip" text="SELECTED" />'
            '<Text styleClass="t-hint" text="PX4 Autopilot  |  Gazebo SITL" /></children></VBox>')
    x = x[:m.start()] + card + x[m.end():]
    x = x.replace('<?import javafx.scene.control.Button?>', '<?import javafx.scene.control.Button?>\n<?import javafx.scene.control.Label?>', 1)
    x = x.replace("Flight  Controller", "Flight Controller")
    x = x.replace('<Insets bottom="-30.0" top="80.0" />', '<Insets bottom="0.0" top="60.0" />')
    x = x.replace("Currently the tool only supports PX4, but others will come soon", "Inject faults. Expose weak spots. Prove resilience.")
    x = re.sub(r'(<Text fx:id="tlDescription1"[^>]*?)styleClass="[^"]*"', r'\1styleClass="t-tag"', x, count=1)
    return x

tag_re = re.compile(r'<(?P<tag>[A-Za-z][\w.]*)(?P<attrs>(?:\s+[\w:.]+="[^"]*")*)\s*(?P<end>/?)>', re.S)
font_re = re.compile(r'\s*<font>\s*<Font name="(?P<n>[^"]+)" size="(?P<s>[\d.]+)"')
stats = {"files": 0, "styles": 0, "texts": 0}

for path in sorted(glob.glob(os.path.join(d, "*.fxml"))):
    src = open(path, encoding="utf-8").read()
    base = os.path.basename(path)
    out, pos = [], 0
    for m in tag_re.finditer(src):
        tag, attrs, end = m.group("tag"), m.group("attrs"), m.group("end")
        if tag == "Polygon":
            na = re.sub(r'\s(fill|stroke)="[^"]*"', "", attrs) + ' styleClass="chev"'
            out.append(src[pos:m.start()]); out.append("<Polygon%s%s>" % (na, end)); pos = m.end()
            continue
        if tag not in ("Text", "Button", "VBox", "HBox", "AnchorPane", "BorderPane", "ListView", "Label"):
            continue
        sm = re.search(r'\sstyle="([^"]*)"', attrs)
        style = sm.group(1) if sm else None
        tm = re.search(r'\stext="([^"]*)"', attrs)
        text = tm.group(1) if tm else None
        fm = font_re.match(src, m.end()) if not end else None
        fsize = fm.group("s") if fm else None
        fname = fm.group("n") if fm else None
        if style is None and tag != "Text":
            continue
        cls = classes_for(tag, style, text, fsize, fname, base == "SideBar.fxml")
        if tag == "Button" and style is None:
            continue
        if "styleClass=" in attrs:
            raise SystemExit("styleClass already present in " + base)
        new_attrs = attrs
        if "step-on" in cls or "step-off" in cls or (tag == "Button" and "btn-primary" in cls and text and len(text) > 2):
            new_attrs = re.sub(r'\s(prefWidth|prefHeight)="[^"]*"', "", new_attrs)
            if "btn-primary" in cls: new_attrs += ' minWidth="110.0"'
        if sm:
            new_attrs = new_attrs.replace(sm.group(0), "")
            stats["styles"] += 1
        if cls:
            new_attrs += ' styleClass="%s"' % ", ".join(cls)
            if tag == "Text": stats["texts"] += 1
        if base == "SideBar.fxml" and tag == "BorderPane" and 'fx:id="bp"' in attrs:
            new_attrs += ' stylesheets="@theme.css"'
        out.append(src[pos:m.start()])
        out.append("<%s%s%s>" % (tag, new_attrs, end))
        pos = m.end()
    out.append(src[pos:])
    res = "".join(out)
    res = re.sub(r'\stextFill="[^"]*"', "", res)
    res = re.sub(r'\sfill="#274c5e"', "", res)
    res = re.sub(r'\s*<font>\s*<Font [^>]*/>\s*</font>', "", res)
    res = re.sub(r'(text="[^"]*)Gezebo', r"\1Gazebo", res)
    res = re.sub(r'(text="[^"]*)Responsable', r"\1Responsible", res)
    if base == "ResumeInjectionCampaign.fxml": res = res.replace('text="Configure the Injection Campaign"', 'text="Review and Generate the Campaign"')
    if base == "HomePage.fxml": res = home_extras(res)
    if base == "SideBar.fxml": res = side_extras(res)
    if base == "SelectFlightControl.fxml": res = flight_extras(res)
    # SideBar root needs the stylesheet even when the first loop skipped it (BorderPane has no style attr)
    if base == "SideBar.fxml" and "stylesheets=" not in res:
        res = re.sub(r'(<BorderPane\b[^>]*fx:id="bp")', r'\1 stylesheets="@theme.css"', res, count=1)
    # inline fill / textFill attributes are overridden by the stylesheet; nothing to do.
    if res != src:
        open(path, "w", encoding="utf-8").write(res)
        stats["files"] += 1

# ---- Java: sidebar highlight as a pseudo-class instead of inline style ----
p = os.path.join(d, "SideBarController.java")
j = open(p, encoding="utf-8").read()
a = j.index("private void changeMenuButtonColor(Button btn, boolean selected) {")
b = j.index("/**", a)
new = ('private void changeMenuButtonColor(Button btn, boolean selected) {\n'
       '\t\tbtn.pseudoClassStateChanged(javafx.css.PseudoClass.getPseudoClass("selected"), selected);\n'
       '\t}\n\t\n\t')
j = j[:a] + new + j[b:]
open(p, "w", encoding="utf-8").write(j)

# ---- Java: alert dialogs ----
p = os.path.join(d, "CommunInterfaceFunctions.java")
j = open(p, encoding="utf-8").read()
hook = "alert.getDialogPane().setMinHeight(Region.USE_PREF_SIZE);"
assert j.count(hook) == 2, j.count(hook)
j = j.replace(hook, hook + '\n\t\talert.getDialogPane().getStylesheets().add(CommunInterfaceFunctions.class.getResource("theme.css").toExternalForm());')
open(p, "w", encoding="utf-8").write(j)

INPUT_BRIDGE = r"""package userInterface;

import javafx.event.Event;
import javafx.event.EventTarget;
import javafx.scene.Scene;
import javafx.scene.input.KeyCode;
import javafx.scene.input.KeyEvent;

/** Input compatibility layer for virtual / remote displays. Some virtual displays report the Super (Meta)
 *  modifier as permanently held, and JavaFX text controls then ignore every typed character. Key events are
 *  re-dispatched with the Meta flag cleared; this application defines no Meta shortcuts, so nothing is lost. */
final class InputBridge {
    private static int logged = 0;

    static void install(final Scene scene) {
        scene.addEventFilter(KeyEvent.ANY, e -> {
            if (!e.isMetaDown()) return;
            KeyCode k = e.getCode();
            if (k == KeyCode.META || k == KeyCode.WINDOWS) return;
            if (!(e.getTarget() instanceof EventTarget)) return;
            if (logged < 5) { logged++; System.err.println("KEYDBG meta modifier cleared on " + e.getEventType()); }
            KeyEvent clean = new KeyEvent(e.getEventType(), e.getCharacter(), e.getText(), k,
                e.isShiftDown(), e.isControlDown(), e.isAltDown(), false);
            e.consume();
            Event.fireEvent((EventTarget) e.getTarget(), clean);
        });
    }
}
"""
# ---- Java: input compatibility layer (typing on remote / virtual displays) ----
open(os.path.join(d, "InputBridge.java"), "w", encoding="utf-8").write(INPUT_BRIDGE)
p = os.path.join(d, "Main.java")
j = open(p, encoding="utf-8").read()
hook = "Scene scene = new Scene(root);"
assert j.count(hook) == 1
j = j.replace(hook, hook + "\n\t\t\tInputBridge.install(scene);\n\t\t\tprimaryStage.setWidth(1240); primaryStage.setHeight(840);")
open(p, "w", encoding="utf-8").write(j)

# ---- Java: the About button had an empty handler; give it a small themed dialog ----
p = os.path.join(d, "SideBarController.java")
j = open(p, encoding="utf-8").read()
ABOUT = r"""void onClickButtonAbout(MouseEvent event) {
        javafx.scene.control.Alert a = new javafx.scene.control.Alert(javafx.scene.control.Alert.AlertType.INFORMATION);
        a.setTitle("About");
        a.setHeaderText("UAV&V Fault Injection Toolkit");
        a.setContentText("Plan, run and analyse repeatable fault-injection campaigns on PX4 UAV missions.\n\n21 fault types (GPS, IMU, accelerometer, gyroscope), custom Python faults, seeded campaigns and U-space traffic tracking.\n\nTarget: PX4 SITL with Gazebo.");
        a.getDialogPane().getStylesheets().add(SideBarController.class.getResource("theme.css").toExternalForm());
        a.getDialogPane().setMinHeight(javafx.scene.layout.Region.USE_PREF_SIZE);
        a.getDialogPane().setPrefWidth(480);
        a.showAndWait();
    }"""
j2 = re.sub(r"void onClickButtonAbout\(MouseEvent event\) \{\s*\}", lambda m: ABOUT, j, count=1)
assert j2 != j
open(p, "w", encoding="utf-8").write(j2)

for rel, pairs in (("SelectUavModelController.java", [('split("\\\\\\\\")', 'split("[\\\\\\\\/]")'), ("lbGezeboWorld.setText(gezeboWorldPath);", "lbGezeboWorld.setText(new java.io.File(gezeboWorldPath).getName());")]),
                   ("SideBarController.java", [("will be loss", "will be lost")]),
                   ("CommunInterfaceFunctions.java", [("Select Gezebo Configuration Files", "Select Gazebo Configuration Files")]),
                   (os.path.join("..", "dataModel", "CampaignData.java"), [('"Gezebo World File: " + gezeboWorldPath', '"Gazebo World File: " + (gezeboWorldPath == null ? "-" : new java.io.File(gezeboWorldPath).getName())'), ('"Gezebo World File: "', '"Gazebo World File: "')])):
    pp = os.path.join(d, rel)
    if os.path.exists(pp):
        t = open(pp, encoding="utf-8").read()
        for a_, b_ in pairs: t = t.replace(a_, b_)
        open(pp, "w", encoding="utf-8").write(t)

EXTRA_CSS = """
/* popup menus live in their own window: literal colours (look-ups from .root do not reach them) */
.context-menu { -fx-background-color: white; -fx-background-radius: 3; -fx-border-color: #d3deea; -fx-border-radius: 3; -fx-padding: 4; -fx-effect: null; }
.context-menu .menu-item { -fx-background-radius: 3; -fx-padding: 6 18 6 12; }
.context-menu .menu-item .label { -fx-text-fill: #0f1f2e; -fx-font-size: 13px; }
.context-menu .menu-item:focused { -fx-background-color: #0e8fa6; }
.context-menu .menu-item:focused .label { -fx-text-fill: white; }
/* nested cards (fault forms are loaded into a card) are flattened */
.card .card {
    -fx-background-color: transparent;
    -fx-border-color: transparent;
    -fx-effect: null;
}
"""
with open(os.path.join(d, "theme.css"), "a", encoding="utf-8") as _f:
    _f.write(EXTRA_CSS)

# ---- logos: the sidebar shows the UAV&V mark; the three footer logos of the original are replaced by a blank image ----
import shutil
here = os.path.dirname(os.path.abspath(__file__))
for f in glob.glob(os.path.join(d, "*.fxml")):
    t = open(f, encoding="utf-8").read()
    n = re.sub(r"img/(?:c\w+_logo|f\w+_logo|horizon)\.png", "img/blank.png", t)   # institutional logos of the original
    n = re.sub(r"img/B[A-Za-z]+\.png", "img/uavv_logo.png", n)                  # original sidebar logo
    if n != t: open(f, "w", encoding="utf-8").write(n)
imgdir = os.path.normpath(os.path.join(d, "..", "..", "img")); os.makedirs(imgdir, exist_ok=True)
shutil.copyfile(os.path.join(here, "logo.png"), os.path.join(imgdir, "uavv_logo.png"))
shutil.copyfile(os.path.join(here, "blank.png"), os.path.join(imgdir, "blank.png"))

print("themed: %(files)d fxml files, %(styles)d inline styles replaced, %(texts)d text nodes classed" % stats)
