import enum
import sdl2  # pyright: ignore[reportMissingTypeStubs]
import sdl2.ext  # pyright: ignore[reportMissingTypeStubs]
from dataclasses import dataclass
from typing import cast

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

class Frame:
    def __init__(self, id:int):
        self.c_lu: int = 0
        self.c_rd: int = 0
        self.direction: Direction = Direction.NONE
        self.ratio:float = 0.0
        self.id: int = id
        self.x:int = 0
        self.y:int = 0
        self.wx:int = 0
        self.hy:int = 0
class Frames:
    def __init__(self, theme:ColorTheme|None = None):
        self.fr_id:int = 0
        self.frames: list[Frame] = []
        self.root_id:int = self.create()
        self.active_id:int = self.root_id
        if theme is None:
            self.theme: ColorTheme = ColorTheme((0, 50, 0), (255, 255, 255), (0,0,255), (255,0,0))
        else:
            self.theme = theme

    def get_id(self) -> int:
        self.fr_id += 1
        return self.fr_id

    def create(self) -> int:
        id:int = self.get_id()
        fr:Frame = Frame(id)
        self.frames.append(fr)
        return id

    def idx(self, id:int) -> int | None:
        for index, fr in enumerate(self.frames):
            if fr.id == id:
                return index
        return None

    def parent_idx(self, id:int) -> int | None:
        for index, fr in enumerate(self.frames):
            if fr.c_lu == id or fr.c_rd == id:
                return index
        return None

    def delete(self, id:int=0) -> bool:
        if id == 0:
            id = self.active_id
        active:bool = False
        if id == self.active_id:
            active = True
        lc = self.idx(id)
        if lc is None:
            return False
        fr = self.frames[lc]
        if fr.c_lu != 0 or fr.c_rd != 0:
            return False
        if fr.id == self.root_id:
            return False
            
        p_idx = self.parent_idx(id)
        if p_idx is None:
            print("Illegal state in delete (1)")
            return False

        p_fr = self.frames[p_idx]
        if p_fr.id == self.root_id:
            if p_fr.c_lu == id:
                self.root_id = p_fr.c_rd
            elif p_fr.c_rd == id:
                self.root_id = p_fr.c_lu
            else:
                print("Illegal state in delete (2)")
                return False
            self.frames.remove(p_fr)
            self.frames.remove(fr)
            if active:
                self.next()
            return True
        else:
            pp_idx = self.parent_idx(p_fr.id)
            if pp_idx is None:
                print("Illegal state in delete (3)")
                return False
            pp_fr = self.frames[pp_idx]
            if p_fr.c_lu == id:
                if pp_fr.c_lu == p_fr.id:
                    pp_fr.c_lu = p_fr.c_rd
                elif pp_fr.c_rd == p_fr.id:
                    pp_fr.c_rd = p_fr.c_rd
                else:
                    print("Illegal state in delete (4)")
                    return False
                self.frames.remove(p_fr)
                self.frames.remove(fr)
            elif p_fr.c_rd == id:
                if pp_fr.c_lu == p_fr.id:
                    pp_fr.c_lu = p_fr.c_lu
                elif pp_fr.c_rd == p_fr.id:
                    pp_fr.c_rd = p_fr.c_lu
                else:
                    print("Illegal state in delete (5)")
                    return False
                self.frames.remove(p_fr)
                self.frames.remove(fr)
            else:
                print("Illegal state in delete (6)")
                return False
            if active:
                self.next()
        return True

    def split(self, id: int=0, direction: Direction = Direction.HORIZONTAL) -> bool:
        if id == 0:
            id = self.active_id
        idx = self.idx(id)
        if idx is None:
            return False
        fr = self.frames[idx]
        if fr.c_lu != 0 or fr.c_rd != 0:
            return False
        fr.direction = direction
        fr.ratio = 0.5
        fr.c_lu = self.create()
        fr.c_rd = self.create()
        if fr.id == self.active_id:
            self.active_id = fr.c_lu
        return True

    def geometry(self, x: int, y: int, wx:int, hy:int):
        print("-------------")
        def _geometry(id: int, x: int, y:int, wx:int, hy: int, level:int):
            f_idx = self.idx(id)
            if f_idx is None:
                print("Internal error (1) in geometry")
                return
            fr: Frame = self.frames[f_idx]
            fr.x = x
            fr.y = y
            fr.wx = wx
            fr.hy = hy
            print(f"{" "*level} id={fr.id} ratio={fr.ratio}, [{x},{y}] {wx}x{hy} ", end="")
            if fr.id == self.active_id:
                print("* ", end="")
            if fr.c_lu != 0 and fr.c_rd != 0:
                print("->")
                if fr.direction == Direction.HORIZONTAL:
                    _geometry(fr.c_lu, fr.x, fr.y, int(fr.wx * fr.ratio), fr.hy, level+1 )
                    _geometry(fr.c_rd, fr.x+int(fr.wx*fr.ratio), fr.y, int(fr.wx * (1-fr.ratio)), fr.hy, level+1 )
                elif fr.direction == Direction.VERTICAL:
                    _geometry(fr.c_lu, fr.x, fr.y, fr.wx, int(fr.hy * fr.ratio), level+1)
                    _geometry(fr.c_rd, fr.x, fr.y+int(fr.hy*fr.ratio), fr.wx, int(fr.hy*(1-fr.ratio)), level+1)
            else:
                if fr.c_lu !=0 or fr.c_rd !=0:
                    print("Illegal state: incomplete sub-tree-node!")
                    return
                print("[w]")

        _geometry(self.root_id, x, y, wx, hy, 0)

    def win_frames(self) -> tuple[list[Frame], int]:
        wfr: list[Frame] = []
        a_idx = -1
        for fr in self.frames:
            if fr.c_lu == 0 and fr.c_rd == 0:
                wfr.append(fr)
                if fr.id == self.active_id:
                    a_idx = len(wfr) - 1
        return (wfr, a_idx)

    def next(self):
        wt: tuple[list[Frame], int] = self.win_frames()
        wfr: list[Frame]
        a_idx:int
        wfr, a_idx = wt
        if a_idx<len(wfr) - 1:
            self.active_id = wfr[a_idx+1].id
        else:
            self.active_id = wfr[0].id
 
    def render(self, renderer: sdl2.ext.Renderer):
        def _render(id:int):
            idx: int | None = self.idx(id)
            if idx is None:
                return
            frame = self.frames[idx]
            rect = sdl2.SDL_Rect(frame.x, frame.y, frame.wx, frame.hy)
            if frame.id == self.active_id:
                renderer.draw_rect(rect, color=self.theme.active_border)  # pyright: ignore[reportUnknownMemberType]
            else:
                renderer.draw_rect(rect, color=self.theme.border)  # pyright: ignore[reportUnknownMemberType]
            if frame.c_lu!=0 and frame.c_rd!=0:
                _render(frame.c_lu)
                _render(frame.c_rd)

        _render(self.root_id)




        

def run():
    sdl2.ext.init()

    window = sdl2.ext.Window("Resizable Window", size=(800, 600), flags=(sdl2.SDL_WINDOW_RESIZABLE | sdl2.SDL_WINDOW_ALLOW_HIGHDPI |  sdl2.SDL_RENDERER_ACCELERATED))
    window.show()
    renderer = sdl2.ext.Renderer(window, flags=sdl2.SDL_RENDERER_ACCELERATED)

    frames = Frames()
    frames.geometry(0, 0, 800, 600)
    _ = frames.split(direction=Direction.HORIZONTAL)
    frames.geometry(0, 0, 800, 600)
    _ = frames.split(direction=Direction.VERTICAL)
    frames.geometry(0, 0, 800, 600)
    _ = frames.split(direction=Direction.HORIZONTAL)
    frames.geometry(0, 0, 800, 600)
    _ = frames.delete()
    frames.geometry(0, 0, 800, 600)

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
                    frames.geometry(0, 0, new_width, new_height)

                    # Update the renderer's logical size to match the new window size
                    renderer.logical_size = (new_width, new_height)
            if event.type == sdl2.SDL_KEYDOWN:
                key_name = cast(str, sdl2.SDL_GetKeyName(event.key.keysym.sym).decode())  # pyright: ignore[reportUnknownMemberType]
                modifiers = cast(int, sdl2.SDL_GetModState())  # pyright: ignore[reportUnknownMemberType]
                wx: int; hy: int
                wx, hy = cast(tuple[int,int], window.size)
                if key_name == 'X' and (modifiers & sdl2.KMOD_LCTRL or modifiers & sdl2.KMOD_RCTRL):
                    print("Ctrl+X pressed, exiting.")
                    running = False
                    break
                if key_name == 'Tab':
                    frames.next()
                    frames.geometry(0,0,wx, hy)
                    break
                if key_name == 'H':
                    _ = frames.split(direction=Direction.HORIZONTAL)
                    frames.geometry(0,0,wx, hy)
                    break
                if key_name == 'V':
                    _ = frames.split(direction=Direction.VERTICAL)
                    frames.geometry(0,0,wx, hy)
                    break
                if key_name == 'C':
                    _ = frames.delete()
                    frames.geometry(0,0,wx, hy)
                    break

                else:
                    print(f"Key pressed: {key_name}")

        renderer.clear((50, 50, 50))  # pyright: ignore[reportUnknownMemberType]
        frames.render(renderer)
        renderer.present()
        sdl2.SDL_Delay(10)  # pyright: ignore[reportUnknownMemberType]

    sdl2.ext.quit()

if __name__ == "__main__":
    run()
