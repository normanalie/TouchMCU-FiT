import subprocess
import sys
import getopt
import os

from touchmcu.master import create_assignment, create_fader_banks, create_master_fader, create_timecode
from touchmcu.touchosc import Rect, ButtonType, ColorEnum, OutlineStyle
from touchmcu.touchosc.controls import Pager, Page, Label
from touchmcu.touchosc.document import Document
from touchmcu.touchosc.midi import MidiNotes

from touchmcu import list_overlays, load_all_scripts, load_overlay
from touchmcu.track import create_track
from touchmcu.controls import create_button, create_cc_fader
from touchmcu.transport import create_actions, create_function_select, create_global_view, create_jog, create_transport, create_transport_assignment, create_transport_timecode


def main(argv):
    try:
        opts, args = getopt.getopt(argv,"hao:s",["help","all","overlay=","show"])
    except getopt.GetoptError:
        print('python -m touchmcu -o <overlay_name>')
        sys.exit(2)

    show = False
    overlay_name = "default"
    all_overlays = False

    for opt, arg in opts:
        if opt == '-h':
            print('python -m touchmcu -o <overlay_name>')
            sys.exit()
        elif opt in ("-o", "--overlay"):
            overlay_name = arg
        elif opt in ("-s", "--show"):
            show = True
        elif opt in ("-a", "--all"):
            all_overlays = True

    if all_overlays:
        todo = list_overlays()
    else:
        todo = [overlay_name]

    os.makedirs("./output")

    for name in todo:
        # ====== OVERLAY ===============================================================

        overlay = load_overlay(name)

        # ====== DOCUMENT ==============================================================

        TRACK_COUNT = 16
        doc = Document(1024 + 102 * (TRACK_COUNT - 8), 768)

        doc.root["script"] = load_all_scripts(
            "table_utils.lua",
            "lcd.lua"
        )

        pager = Pager(
            parent=doc.root,
            name="pager",
            frame=doc.root["frame"]
        )

        # ====== TRACKS ================================================================

        track_page = Page(
            parent=pager,
            name="track_page",
            tabLabel="Tracks",
            frame=Rect(
                x=0,
                y=pager["tabbarSize"],
                w=pager["frame"]["w"],
                h=pager["frame"]["h"] - pager["tabbarSize"]
            )
        )

        for i in range(TRACK_COUNT):
            tr = create_track(track_page, overlay, i)
            tr["frame"].move(2 + 102 * i, 0)

        base_x = 820 + 102 * (TRACK_COUNT - 8)

        timecode = create_timecode(track_page, overlay)
        timecode["frame"].move(base_x, 0)

        assign = create_assignment(track_page, overlay)
        assign["frame"].move(base_x, 106)

        banks = create_fader_banks(track_page, overlay)
        banks["frame"].move(base_x, 342)

        master = create_master_fader(track_page)
        master["frame"].move(base_x + 102, 342)

        # ====== TRANSPORT =============================================================

        transport_page = Page(
            parent=pager,
            name="transport_page",
            tabLabel="Transport",
            frame=Rect(
                x=0,
                y=pager["tabbarSize"],
                w=pager["frame"]["w"],
                h=pager["frame"]["h"] - pager["tabbarSize"]
            )
        )

        functions = create_function_select(transport_page, overlay)
        functions["frame"].move(2, 2)

        global_view = create_global_view(transport_page, overlay)
        global_view["frame"].move(2, 122)

        actions = create_actions(transport_page, overlay)
        actions["frame"].move(2, 242)

        transport = create_transport(transport_page, overlay)
        transport["frame"].move(2, 422)

        timcode = create_transport_timecode(transport_page, overlay)
        timcode["frame"].move(678, 2)

        assign = create_transport_assignment(transport_page, overlay)
        assign["frame"].move(678, 122)

        jog = create_jog(transport_page, overlay)
        jog["frame"].move(678, 242)

        # ====== NOTES ========================================================
        notes_page = Page(
            parent=pager,
            name="notes_page",
            tabLabel="Notes",
            frame=Rect(
                x=0,
                y=pager["tabbarSize"],
                w=pager["frame"]["w"],
                h=pager["frame"]["h"] - pager["tabbarSize"]
            )
        )

        NOTE_W = 100
        NOTE_H = 40
        for i in range(128):
            x = 2 + (i % 16) * (NOTE_W + 12)
            y = 2 + (i // 16) * (NOTE_H + 8)
            create_button(
                notes_page,
                name=f"note_{i}",
                note=i,
                frame=Rect(x=x, y=y, w=NOTE_W, h=NOTE_H),
                label=str(i),
                type=ButtonType.MOMENTARY
            )

        # ====== CC FADERS =====================================================
        cc_page = Page(
            parent=pager,
            name="cc_page",
            tabLabel="CC",
            frame=Rect(
                x=0,
                y=pager["tabbarSize"],
                w=pager["frame"]["w"],
                h=pager["frame"]["h"] - pager["tabbarSize"]
            )
        )

        CC_W = 60
        CC_H = 350
        cc_numbers = (
            list(range(16, 32)) +
            list(range(72, 81)) +
            [83, 86] +
            list(range(88, 96)) +
            list(range(116, 128))
        )

        for idx, cc in enumerate(cc_numbers):
            x = 2 + (idx % 16) * (CC_W + 12)
            y = 2 + (idx // 16) * (CC_H + 50)
            create_cc_fader(
                cc_page,
                name=f"cc_{cc}",
                cc=cc,
                frame=Rect(x=x, y=y, w=CC_W, h=CC_H)
            )
            lb = Label(
                parent=cc_page,
                name=f"lb_cc_{cc}",
                frame=Rect(x=x, y=y + CC_H + 2, w=CC_W, h=20),
                color=ColorEnum.GREY.value,
                outline=True,
                outlineStyle=OutlineStyle.EDGES
            )
            lb["text"] = str(cc)


        # ==============================================================================

        fn = f"./output/{overlay['overlay_title']}.tosc"

        doc.finalise()
        doc.save(fn)

        if show:
            subprocess.call(["open", fn])

if __name__ == "__main__":
    main(sys.argv[1:])
