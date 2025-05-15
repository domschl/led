import enum
import sdl2  # pyright: ignore[reportMissingTypeStubs]
import sdl2.ext  # pyright: ignore[reportMissingTypeStubs]
from dataclasses import dataclass
from typing import cast, override

@dataclass
class ColorTheme:
    background: tuple[int, int, int]
    foreground: tuple[int, int, int]
    border: tuple[int, int, int]
    active_border: tuple[int, int, int]

Direction = enum.Enum('Direction', 'NONE HORIZONTAL VERTICAL')
# forward declaration of LFrame
# class LFrame:
#     pass

class Content:
    def __init__(self, name: str):
        self.name: str = name
        self.data: dict[str, str] = {}

    def set_data(self, key: str, value: str):
        self.data[key] = value

    def get_data(self, key: str) -> str | None:
        return self.data.get(key)

    @override
    def __repr__(self):
        return f"Content(name={self.name}, data={self.data})"

class LFrame:  # pyright: ignore[reportRedeclaration]
    pass

class LFrame:
    def __init__(self, parent: LFrame | None=None, content: Content | None=None, active: bool=False):
        self.active: bool = active
        self.parent: LFrame | None = parent
        self.lc: LFrame | None = None
        self.rc: LFrame | None = None
        self.ratio: float = 0
        self.dir: Direction = Direction.NONE
        self.x: int = 0
        self.y: int = 0
        self.w: int = 0
        self.h: int = 0
        self.content: Content | None = content

    def inherit(self, frame: LFrame):
        self.active = frame.active
        self.parent = frame.parent
        self.lc = frame.lc
        self.rc = frame.rc
        self.ratio = frame.ratio
        self.dir = frame.dir
        self.x = frame.x
        self.y = frame.y
        self.w = frame.w
        self.h = frame.h
        self.content = frame.content

    def split(self, dir: Direction = Direction.HORIZONTAL) -> None:
        self.lc = LFrame(parent=self, content=self.content, active=self.active)
        self.rc = LFrame(parent=self)
        self.ratio = 0.5
        self.dir = dir
        self.content = None
        self.active = False

    def close(self):
        if self.rc is not None or self.lc is not None:
            return
        if self.parent is None:
            return
        if self.parent.lc is self:
            self.parent.lc = None
            if self.parent.rc is None:
                self.parent.ratio = 0
                self.parent.dir = Direction.NONE                
            else:
                old_parent = self.parent.parent
                self.parent.inherit(self.parent.rc)
                self.parent.parent = old_parent
        elif self.parent.rc is self:
            self.parent.rc = None
            if self.parent.lc is None:
                self.parent.ratio = 0
                self.parent.dir = Direction.NONE
            else:
                old_parent = self.parent.parent
                self.parent.inherit(self.parent.lc)
                self.parent.parent = old_parent
        else:
            print("bad state close")
        if self.active is True:
            self.parent.active = True
        self.parent = None
        self.lc = None
        self.rc = None
        self.ratio = 0
        self.dir = Direction.NONE
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0
        self.content = None
        self.active = False

    def set_ratio(self, ratio: float):
        self.ratio = ratio

class LFrames:
    def __init__(self, parent: LFrame | None=None, theme: ColorTheme | None=None):
        self.root_frame: LFrame | None = None
        if parent is None:
            self.root_frame = LFrame(parent=None, content=Content("<root>"), active=True)
        else:
            self.root_frame = parent
        if theme is None:
            self.theme: ColorTheme = ColorTheme((0, 50, 0), (255, 255, 255), (0,0,255), (255,0,0))
        else:
            self.theme = theme

    def geometry(self, x: int, y: int, w: int, h: int, frame: LFrame | None = None):
        if frame is None:
            frame = self.root_frame
        def _geometry(x: int, y: int, w: int, h: int, frame: LFrame | None = None, level: int = 0):
            if frame is None:
                return
            if frame.active is True:
                b = "*"
            else:
                b = " "
            print(f"frame_geometry: {" "*level}[{x},{y}]->{w}x{h} {b} ", end="")
            if frame.rc is not None or frame.lc is not None:
                print("->")
                if frame.dir == Direction.VERTICAL:
                    nw: int = w
                    nh_l = int(h * frame.ratio)
                    nh_r = int(h * (1 - frame.ratio))
                    nx = x
                    ny_l = y
                    ny_r = y + int(h * frame.ratio)
                    _geometry(nx, ny_l, nw, nh_l, frame.lc, level + 1)
                    _geometry(nx, ny_r, nw, nh_r, frame.rc, level + 1)
                    frame.x = 0
                    frame.y = 0
                    frame.w = 0
                    frame.h = 0
                elif frame.dir == Direction.HORIZONTAL:
                    nw_l = int(w * frame.ratio)
                    nw_r = int(w * (1 - frame.ratio))
                    nx_l = x
                    nx_r = x + int(w * frame.ratio)
                    ny = y
                    nh = h
                    _geometry(nx_l, ny, nw_l, nh, frame.lc, level + 1)
                    _geometry(nx_r, ny, nw_r, nh, frame.rc, level + 1)
                    frame.x = 0
                    frame.y = 0
                    frame.w = 0
                    frame.h = 0
                else:
                    print("bad state")
            else:
                print("<<")
                frame.x = x
                frame.y = y
                frame.w = w
                frame.h = h

        _geometry(x, y, w, h, frame)

    def render(self, frame: LFrame | None, renderer: sdl2.ext.Renderer):
        if frame is None:
            frame = self.root_frame
        def _render(frame: LFrame | None, renderer: sdl2.ext.Renderer):
            if frame is None:
                return
            if frame.rc is not None or frame.lc is not None:
                if frame.dir == Direction.VERTICAL:
                    _render(frame.lc, renderer)
                    _render(frame.rc, renderer)
                elif frame.dir == Direction.HORIZONTAL:
                    _render(frame.lc, renderer)
                    _render(frame.rc, renderer)
                else:
                    print("bad state render")
            else:
                rect = sdl2.SDL_Rect(frame.x, frame.y, frame.w, frame.h)
                if frame.active is True:
                    renderer.draw_rect(rect, color=self.theme.active_border)  # pyright: ignore[reportUnknownMemberType]
                else:
                    renderer.draw_rect(rect, color=self.theme.border)  # pyright: ignore[reportUnknownMemberType]

        _render(frame, renderer)

    def list(self) -> list[LFrame]:
        frames: list[LFrame] = []
        def _list(frame: LFrame | None):
            if frame is None:
                return
            if frame.lc is None and frame.rc is None:
                frames.append(frame)
            if frame.rc is not None or frame.lc is not None:
                if frame.dir == Direction.VERTICAL:
                    _list(frame.lc)
                    _list(frame.rc)
                elif frame.dir == Direction.HORIZONTAL:
                    _list(frame.lc)
                    _list(frame.rc)
                else:
                    print("bad state list")
        _list(self.root_frame)
        return frames

    def circle_active(self):
        frame_list = self.list()
        for index, frame in enumerate(frame_list):
            if frame.active is True:
                frame.active = False
                if index + 1 < len(frame_list):
                    frame_list[index + 1].active = True
                else:
                    frame_list[0].active = True
                break

    def get_active(self) -> LFrame | None:
        frame_list = self.list()
        for frame in frame_list:
            if frame.active is True:
                return frame
        return None

    def split(self, dir: Direction = Direction.HORIZONTAL):
        cur_fame = self.get_active()
        if cur_fame is None:
            print("no active frame to split")
            return
        if cur_fame.lc is not None or cur_fame.rc is not None:
            print("cannot split an already split frame")
            return
        cur_fame.split(dir)

    def compact_tree(self):
        if self.root_frame is None:
            return
        def _replace_child(parent: LFrame, child: LFrame, new_child: LFrame):
            if parent.lc is not None:
                if parent.lc is child:
                    parent.lc = new_child
                else:
                    _replace_child(parent.lc, child, new_child)
            if parent.rc is not None:
                if parent.rc is child:
                    parent.rc = new_child
                else:
                    _replace_child(parent.rc, child, new_child)
        def _compact_tree_helper(self, frame: LFrame ) -> None:
            if frame.lc is None and frame.rc is not None:
                if frame.parent is None:
                    self.root_frame = frame.rc
                else:
                    _replace_child(self.root_frame, frame, frame.rc)
                del frame
            elif frame.rc is None and frame.lc is not None:
                if frame.parent is None:
                    self.root_frame = frame.lc
                else:
                    _replace_child(self.root_frame, frame, frame.lc)
                del frame
            else:
                if frame.lc is not None:
                    _compact_tree_helper(self, frame.lc)
                if frame.rc is not None:
                    _compact_tree_helper(self, frame.rc)
        _compact_tree_helper(self, self.root_frame)

    def close(self):
        cur_frame = self.get_active()
        if cur_frame is None:
            print("no active frame to close")
            return
        cur_frame.close()
        self.compact_tree()

def run():
    sdl2.ext.init()

    window = sdl2.ext.Window("Resizable Window", size=(800, 600), flags=(sdl2.SDL_WINDOW_RESIZABLE | sdl2.SDL_WINDOW_ALLOW_HIGHDPI |  sdl2.SDL_RENDERER_ACCELERATED))

    window.show()
    frames = LFrames()
    if frames.root_frame is not None:
        frames.root_frame.split(Direction.VERTICAL)
        # if frames.root_frame.lc is not None:
        #     frames.root_frame.lc.split(Direction.HORIZONTAL)
        # if frames.root_frame.rc is not None:
        #     frames.root_frame.rc.split(Direction.VERTICAL)
    frames.geometry(0, 0, 800, 600)
    renderer = sdl2.ext.Renderer(window, flags=sdl2.SDL_RENDERER_ACCELERATED)

    running = True
    while running:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
                break
            if event.type == sdl2.SDL_WINDOWEVENT:
                if event.window.event == sdl2.SDL_WINDOWEVENT_RESIZED:
                    new_width: int = cast(int, event.window.data1)
                    new_height: int = cast(int, event.window.data2)
                    print(f"Window resized to: {new_width}x{new_height}")
                    window.size = (new_width, new_height)
                    # Update the renderer's logical size to match the new window size
                    renderer.logical_size = (new_width, new_height)
                    frames.geometry(0, 0, new_width, new_height)
            if event.type == sdl2.SDL_KEYDOWN:
                key_name = cast(str, sdl2.SDL_GetKeyName(event.key.keysym.sym).decode())  # pyright: ignore[reportUnknownMemberType]
                modifiers = cast(int, sdl2.SDL_GetModState())  # pyright: ignore[reportUnknownMemberType]
                ww: int; wh: int
                ww, wh = cast(tuple[int,int], window.size)
                if key_name == 'X' and (modifiers & sdl2.KMOD_LCTRL or modifiers & sdl2.KMOD_RCTRL):
                    print("Ctrl+X pressed, exiting.")
                    running = False
                    break
                if key_name == 'Tab':
                    frames.circle_active()
                    break
                if key_name == 'H':
                    frames.split(Direction.HORIZONTAL)
                    frames.geometry(0, 0, ww, wh)
                    break
                if key_name == 'V':
                    frames.split(Direction.VERTICAL)
                    frames.geometry(0, 0, ww, wh)
                    break
                if key_name == 'C':
                    frames.close()
                    frames.geometry(0, 0, ww, wh)
                    break

                else:
                    print(f"Key pressed: {key_name}")

        renderer.clear((50, 50, 50))  # pyright: ignore[reportUnknownMemberType]
        frames.render(None, renderer)
        renderer.present()
        sdl2.SDL_Delay(10)  # pyright: ignore[reportUnknownMemberType]

    sdl2.ext.quit()

if __name__ == "__main__":
    run()
