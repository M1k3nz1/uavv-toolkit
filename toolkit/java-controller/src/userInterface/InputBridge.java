package userInterface;

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
