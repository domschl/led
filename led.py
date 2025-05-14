import enum
from pickle import DICT
import sdl2
import sdl2.ext


Direction = enum.Enum('Direction', 'HORIZONTAL VERTICAL')
# forward declaration of LFrame
class LFrame:
    pass

root_frame: LFrame | None = None

class LFrame():
    def __init__(self, parent: LFrame | None=None):
        self.parent: LFrame | None = parent
        self.rc: LFrame | None = None
        self.lc: LFrame | None = None
        self.ratio: float = 0
        self.dir: Direction = Direction.HORIZONTAL
        self.x: int = 0
        self.y: int = 0
        self.w: int = 0
        self.h: int = 0
        if parent is None:
            root_frame = self

    def split(self, dir: Direction = Direction.HORIZONTAL):
        self.rc = LFrame(self)
        self.lc = LFrame(self)
        self.ratio = 0.5
        self.dir = dir

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

def frame_geometry(x: int, y: int, w: int, h: int, frame: LFrame | None = None, level: int = 0):
    print(f"frame_geometry: {" "*level}{x}x{y}->{w}x{h}", end="")
    if frame is None:
        return
    if frame.rc is not None or frame.lc is not None:
        print("->")
        if frame.dir == Direction.VERTICAL:
            frame_geometry(x, y, w, int(h * frame.ratio), frame.rc, level + 1)
            frame_geometry(x, y + int(h * frame.ratio), w, int(h * (1 - frame.ratio)), frame.lc, level + 1)
        else:
            frame_geometry(x, y, int(w * frame.ratio), h, frame.rc, level + 1)
            frame_geometry(x + int(w * frame.ratio), y, int(w * (1 - frame.ratio)), h, frame.lc, level + 1)
    else:
        print("<<")
        frame.x = 0
        frame.y = 0
        frame.w = w
        frame.h = h

def frame_render(frame: LFrame | None, renderer: sdl2.ext.Renderer):
    if frame is None:
        return
    if frame.rc is not None or frame.lc is not None:
        if frame.dir == Direction.VERTICAL:
            frame_render(frame.rc, renderer)
            frame_render(frame.lc, renderer)
        else:
            frame_render(frame.rc, renderer)
            frame_render(frame.lc, renderer)
    else:
        # Render the frame
        rect = sdl2.SDL_Rect(frame.x, frame.y, frame.w, frame.h)
        # print(f"Rendering frame at ({frame.x}, {frame.y}) with size ({frame.w}, {frame.h})")
        renderer.draw_rect(rect, (255, 255, 255)) # Draw white rectangle

def run():
    sdl2.ext.init()

    window = sdl2.ext.Window("Resizable Window", size=(800, 600), flags=(sdl2.SDL_WINDOW_RESIZABLE | sdl2.SDL_WINDOW_ALLOW_HIGHDPI |  sdl2.SDL_RENDERER_ACCELERATED)) # pyright: ignore[reportAny] # sdl2.SDL_WINDOW_RESIZABLE)) #  | sdl2.SDL_WINDOW_METAL |

    window.show()
    global root_frame
    root_frame = LFrame()
    root_frame.split()
    root_frame.rc.split(Direction.HORIZONTAL)
    root_frame.rc.rc.split(Direction.VERTICAL)
    frame_geometry(0, 0, 800, 600, root_frame)

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
                    frame_geometry(0, 0, new_width, new_height, root_frame)
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

        frame_render(root_frame, renderer)
        renderer.present()
        sdl2.SDL_Delay(10) # Small delay to prevent high CPU usage

    sdl2.ext.quit()

if __name__ == "__main__":
    run()
