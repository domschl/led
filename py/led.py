import enum
import sdl2
import sdl2.ext
from dataclasses import dataclass

@dataclass
class ColorTheme:
    background: tuple[int, int, int]
    foreground: tuple[int, int, int]
    border: tuple[int, int, int]
    active_border: tuple[int, int, int]

Direction = enum.Enum('Direction', 'NONE HORIZONTAL VERTICAL')
# forward declaration of LFrame
class LFrame:
    pass

class Content:
    def __init__(self, name: str):
        self.name: str = name
        self.data: dict[str, str] = {}

    def set_data(self, key: str, value: str):
        self.data[key] = value

    def get_data(self, key: str) -> str | None:
        return self.data.get(key)

    def __repr__(self):
        return f"Content(name={self.name}, data={self.data})"

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
        if self.parent.rc is self:
            self.parent.rc = None
        elif self.parent.lc is self:
            self.parent.lc = None
        self.parent = None

    def set_ratio(self, ratio: float):
        self.ratio = ratio

class LFrames:
    def __init__(self, parent: LFrame | None=None, theme: ColorTheme | None=None):
        if parent is None:
            self.root_frame: LFrame = LFrame(parent=None, content=Content("<root>"), active=True)
        else:
            self.root_frame: LFrame = parent
        if theme is None:
            self.theme: ColorTheme = ColorTheme((0, 50, 0), (255, 255, 255), (0,0,255), (255,0,0))
        else:
            self.theme = theme

    def _frame_geometry(self, x: int, y: int, w: int, h: int, frame: LFrame | None = None, level: int = 0):
        print(f"frame_geometry: {" "*level}[{x},{y}]->{w}x{h}", end="")
        if frame is None:
            return
        if frame.rc is not None or frame.lc is not None:
            print("->")
            if frame.dir == Direction.VERTICAL:
                nw: int = w
                nh_l = int(h * frame.ratio)
                nh_r = int(h * (1 - frame.ratio))
                nx = x
                ny_l = y
                ny_r = y + int(h * frame.ratio)
                self._frame_geometry(nx, ny_l, nw, nh_l, frame.lc, level + 1)
                self._frame_geometry(nx, ny_r, nw, nh_r, frame.rc, level + 1)
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
                self._frame_geometry(nx_l, ny, nw_l, nh, frame.lc, level + 1)
                self._frame_geometry(nx_r, ny, nw_r, nh, frame.rc, level + 1)
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

    def _frame_render(self, frame: LFrame | None, renderer: sdl2.ext.Renderer):
        if frame is None:
            return
        if frame.rc is not None or frame.lc is not None:
            if frame.dir == Direction.VERTICAL:
                self._frame_render(frame.lc, renderer)
                self._frame_render(frame.rc, renderer)
            elif frame.dir == Direction.HORIZONTAL:
                self._frame_render(frame.lc, renderer)
                self._frame_render(frame.rc, renderer)
            else:
                print("bad state render")
        else:
            # Render the frame
            rect = sdl2.SDL_Rect(frame.x, frame.y, frame.w, frame.h)
            # renderer.set_draw_color(self.theme.background) # Set background color
            if frame.active is True:
                # print(f"Rendering active frame at ({frame.x}, {frame.y}) with size ({frame.w}, {frame.h})")
                renderer.draw_rect(rect, color=self.theme.active_border) # Draw border rectangle
            else:
                # print(f"Rendering inactive frame at ({frame.x}, {frame.y}) with size ({frame.w}, {frame.h})")
                renderer.draw_rect(rect, color=self.theme.border) # Draw border rectangle

    def frame_geometry(self, x: int, y: int, w: int, h: int, frame: LFrame | None = None):
        if frame is None:
            frame = self.root_frame
        self._frame_geometry(x, y, w, h, frame)

    def frame_render(self, frame: LFrame | None, renderer: sdl2.ext.Renderer):
        if frame is None:
            frame = self.root_frame
        self._frame_render(frame, renderer)

def run():
    sdl2.ext.init()

    window = sdl2.ext.Window("Resizable Window", size=(800, 600), flags=(sdl2.SDL_WINDOW_RESIZABLE | sdl2.SDL_WINDOW_ALLOW_HIGHDPI |  sdl2.SDL_RENDERER_ACCELERATED)) # pyright: ignore[reportAny] # sdl2.SDL_WINDOW_RESIZABLE)) #  | sdl2.SDL_WINDOW_METAL |

    window.show()
    frames = LFrames()
    frames.root_frame.split(Direction.VERTICAL)
    if frames.root_frame.lc is not None:
        frames.root_frame.lc.split(Direction.HORIZONTAL)
    if frames.root_frame.rc is not None:
        frames.root_frame.rc.split(Direction.VERTICAL)
    frames.frame_geometry(0, 0, 800, 600)
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
                    new_width = event.window.data1
                    new_height = event.window.data2
                    print(f"Window resized to: {new_width}x{new_height}")
                    window.size = (new_width, new_height)
                    # Update the renderer's logical size to match the new window size
                    renderer.logical_size = (new_width, new_height)
                    frames.frame_geometry(0, 0, new_width, new_height)
            if event.type == sdl2.SDL_KEYDOWN:
                key_name = sdl2.SDL_GetKeyName(event.key.keysym.sym).decode()
                modifiers = sdl2.SDL_GetModState()
                if key_name == 'X' and (modifiers & sdl2.KMOD_LCTRL or modifiers & sdl2.KMOD_RCTRL):
                    print("Ctrl+X pressed, exiting.")
                    running = False
                    break
                else:
                    print(f"Key pressed: {key_name}")


        # Your drawing code would go here
        # For now, let's just clear the screen with a color
        renderer.clear((50, 50, 50)) # Clear with a dark gray

        frames.frame_render(None, renderer)
        renderer.present()
        sdl2.SDL_Delay(10) # Small delay to prevent high CPU usage

    sdl2.ext.quit()

if __name__ == "__main__":
    run()
