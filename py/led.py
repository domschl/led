import os
import logging
import enum
import ctypes

from dataclasses import dataclass
from typing import cast

import sdl2  # pyright: ignore[reportMissingTypeStubs]
import sdl2.ext  # pyright: ignore[reportMissingTypeStubs]
import sdl2.sdlttf  # pyright: ignore[reportMissingTypeStubs]

@dataclass
class ColorTheme:
    background: tuple[int, int, int, int]
    foreground: tuple[int, int, int, int]
    border: tuple[int, int, int, int]
    active_border: tuple[int, int, int, int]
    cursor: tuple[int, int, int, int]

default_color_theme = ColorTheme((0, 50, 0, 255), (255, 255, 255, 255), (0,0,255,255), (255,0,0,255), (255,255,0,255))

Direction = enum.Enum('Direction', 'NONE HORIZONTAL VERTICAL')
ContentType = enum.Enum('ContentType', 'NONE CELLARRAY TEXT SCHMEME PYTHON')

class ContentCellArray:  # pyright: ignore[reportRedeclaration]
    pass

class ContentCellArray:
    def __init__(self, contents: list[str | ContentCellArray], direction: Direction, content_type: ContentType):
        self.c_lu: int = 0
        self.c_rd: int = 0
        self.direction: Direction = direction
        self.c_type: ContentType = content_type
        self.content: list[str | ContentCellArray] = contents
        self.wx: int = 0
        self.hy: int = 0

class Content:
    def __init__(self):
        self.log: logging.Logger = logging.getLogger("Content")
        self.cell_arrays: dict[str, ContentCellArray] = {}

    def _tokenize_text(self, text:str) -> ContentCellArray:
        arrays: ContentCellArray = ContentCellArray([], Direction.VERTICAL, ContentType.CELLARRAY)
        lines = text.splitlines()
        text_separators = [" ", ",", ".", ";", ":", "(", ")", "{", "}", "[", "]", "<", ">", "|", "/", "\\", "\t"]
        for line in lines:
            tok = ""
            current_array: ContentCellArray = ContentCellArray([], Direction.HORIZONTAL, ContentType.TEXT)
            for char in line:
                if char in text_separators:
                    if tok:
                        current_array.content.append(tok)
                        tok = ""
                else:
                    tok += char
            if tok:
                current_array.content.append(tok)
            arrays.content.append(current_array)
        return arrays

    def get_file_type(self, filename: str) -> ContentType:
        known_extensions = ['.txt', '.scm', '.py']
        if not any(filename.endswith(ext) for ext in known_extensions):
            self.log.error(f"Unknown file type: {filename}")
            return ContentType.NONE
        else:
            if filename.endswith('.txt'):
                return ContentType.TEXT
            elif filename.endswith('.scm'):
                return ContentType.SCHMEME
            elif filename.endswith('.py'):
                return ContentType.PYTHON
            else:
                self.log.error(f"Unknown file type: {filename}")
                return ContentType.NONE

    def tokenize(self, text:str, content_type:ContentType) -> ContentCellArray:
        if content_type == ContentType.TEXT:
            return self._tokenize_text(text)
        elif content_type == ContentType.SCHMEME:
            # Placeholder for actual SchMeme tokenization
            self.log.warning("SchMeme tokenization not implemented, using text tokenizer.")
            return self._tokenize_text(text)
        elif content_type == ContentType.PYTHON:
            # Placeholder for actual Python tokenization
            self.log.warning("Python tokenization not implemented, using text tokenizer.")
            return self._tokenize_text(text)
        else:
            self.log.error(f"Unknown content type: {content_type}")
            return ContentCellArray([], Direction.VERTICAL, ContentType.NONE)

    def load_text_file(self, filename: str):
        try:
            with open(filename, 'r') as file:
                lines = file.read()
            content_type = self.get_file_type(filename)
            self.cell_arrays[filename] = self.tokenize(lines, content_type)

        except FileNotFoundError:
            self.log.error(f"File {filename} not found.")
        except Exception as e:
            self.log.error(f"An error occurred: {e}")

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
    def __init__(self, theme:ColorTheme = default_color_theme):
        self.log: logging.Logger = logging.getLogger("Frames")
        self.fr_id:int = 0
        self.frames: list[Frame] = []
        self.root_id:int = self.create()
        self.active_id:int = self.root_id
        self.theme: ColorTheme = theme

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
            self.log.error("Illegal state in delete (1)")
            return False

        p_fr = self.frames[p_idx]
        if p_fr.id == self.root_id:
            if p_fr.c_lu == id:
                self.root_id = p_fr.c_rd
            elif p_fr.c_rd == id:
                self.root_id = p_fr.c_lu
            else:
                self.log.error("Illegal state in delete (2)")
                return False
            self.frames.remove(p_fr)
            self.frames.remove(fr)
            if active:
                self.next()
            return True
        else:
            pp_idx = self.parent_idx(p_fr.id)
            if pp_idx is None:
                self.log.error("Illegal state in delete (3)")
                return False
            pp_fr = self.frames[pp_idx]
            if p_fr.c_lu == id:
                if pp_fr.c_lu == p_fr.id:
                    pp_fr.c_lu = p_fr.c_rd
                elif pp_fr.c_rd == p_fr.id:
                    pp_fr.c_rd = p_fr.c_rd
                else:
                    self.log.error("Illegal state in delete (4)")
                    return False
                self.frames.remove(p_fr)
                self.frames.remove(fr)
            elif p_fr.c_rd == id:
                if pp_fr.c_lu == p_fr.id:
                    pp_fr.c_lu = p_fr.c_lu
                elif pp_fr.c_rd == p_fr.id:
                    pp_fr.c_rd = p_fr.c_lu
                else:
                    self.log.error("Illegal state in delete (5)")
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

    def size(self, id:int=0, delta:float=0.0):
        if id==0:
            id = self.active_id
        if id == self.root_id:
            return
        if delta == 0.0:
            return
        p_idx = self.parent_idx(id)
        if p_idx is None:
            return
        p_fr = self.frames[p_idx]
        if p_fr.c_lu == id:
            if delta > 0:
                if p_fr.ratio + delta < 0.8:
                    p_fr.ratio += delta
            else:
                if p_fr.ratio + delta > 0.2:
                    p_fr.ratio += delta
        elif p_fr.c_rd == id:
            if delta > 0:
                if p_fr.ratio - delta > 0.2:
                    p_fr.ratio -= delta
            else:
                if p_fr.ratio - delta < 0.8:
                    p_fr.ratio -= delta

    def geometry(self, x: int, y: int, wx:int, hy:int):
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
            if fr.c_lu != 0 and fr.c_rd != 0:
                if fr.direction == Direction.HORIZONTAL:
                    _geometry(fr.c_lu, fr.x, fr.y, int(fr.wx * fr.ratio), fr.hy, level+1 )
                    _geometry(fr.c_rd, fr.x+int(fr.wx*fr.ratio), fr.y, int(fr.wx * (1-fr.ratio)), fr.hy, level+1 )
                elif fr.direction == Direction.VERTICAL:
                    _geometry(fr.c_lu, fr.x, fr.y, fr.wx, int(fr.hy * fr.ratio), level+1)
                    _geometry(fr.c_rd, fr.x, fr.y+int(fr.hy*fr.ratio), fr.wx, int(fr.hy*(1-fr.ratio)), level+1)
            else:
                if fr.c_lu !=0 or fr.c_rd !=0:
                    self.log.error("Illegal state: incomplete sub-tree-node in geometry!")
                    return

        _geometry(self.root_id, x, y, wx, hy, 0)

    def display_geometry(self):
        def _display_geometry(id:int, level:int):
            f_idx = self.idx(id)
            if f_idx is None:
                print("Internal error (1) in geometry")
                return
            fr: Frame = self.frames[f_idx]
            print(f"{" "*level} id={fr.id} ratio={fr.ratio}, [{fr.x},{fr.y}] {fr.wx}x{fr.hy} ", end="")
            if fr.id == self.active_id:
                print("* ", end="")
            if fr.c_lu != 0 and fr.c_rd != 0:
                print("->")
                _display_geometry(fr.c_lu, level+1)
                _display_geometry(fr.c_rd, level+1)
            else:
                if fr.c_lu !=0 or fr.c_rd !=0:
                    print("Illegal state: incomplete sub-tree-node!")
                    return
                print("[w]")

        _display_geometry(self.root_id, 0)

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
 
class FrameRenderer:
    def __init__(self, w:int, h:int, renderer: sdl2.ext.Renderer, font_path:str, theme:ColorTheme=default_color_theme):
        self.log: logging.Logger = logging.getLogger("FrameRenderer")
        self.theme: ColorTheme = theme
        self.renderer: sdl2.ext.Renderer = renderer
        rw: ctypes.c_int = ctypes.c_int(0)
        rh: ctypes.c_int = ctypes.c_int(0)
        sdl2.SDL_GetRendererOutputSize(self.renderer.sdlrenderer, rw, rh);  # pyright: ignore[reportUnknownMemberType]
        if rw.value != w:
            widthScale = rw.value / w
            heightScale = rh.value / h

            if widthScale != heightScale:
                self.log.warning(f"WARNING: width scale {widthScale} != height scale {heightScale}")
            else:
                self.log.info(f"Scale: {widthScale}")
            # sdl2.SDL_RenderSetScale(self.renderer.sdlrenderer, widthScale, heightScale);
        if os.path.exists(font_path) is False:
            self.log.error(f"Font {font_path} does not exist")
        # sdl2.ext.RenderSetScale(self.renderer,2,2)
        self.font_mag:int = 2
        self.dpi:int = 144
        font_size = 8 * self.font_mag
        self.font: sdl2.sdlttf.TTF_Font = sdl2.sdlttf.TTF_OpenFontDPI(font_path.encode('utf-8'), font_size, self.dpi, self.dpi)  # pyright: ignore[reportUnknownMemberType] # , reportUnannotatedClassAttribute]
        sdl2.sdlttf.TTF_SetFontHinting(self.font, sdl2.sdlttf.TTF_HINTING_LIGHT_SUBPIXEL)  # pyright: ignore[reportUnknownMemberType]
        rect = self.render_text("a", 0, 0)
        if rect is not None:
            self.char_width: int = rect.w
            self.char_height: int = rect.h
            self.log.info(f"Char-sizes: {self.char_width}, {self.char_height}")
        else:
            self.log.error("Cannot determine character dimensions!")
        self.line_spacing_extra:int = 0
        script = "Tibt".encode('utf-8')
        sdl2.sdlttf.TTF_SetFontScriptName(self.font, script)  # pyright:ignore[reportUnknownMemberType]

    def render_text(self, text:str, x:int, y:int) -> sdl2.SDL_Rect | None:
        if text == "":
            return
        color_fg = sdl2.SDL_Color(self.theme.foreground[0], self.theme.foreground[1], self.theme.foreground[2], self.theme.foreground[3])
        color_bg = sdl2.SDL_Color(self.theme.background[0], self.theme.background[1], self.theme.background[2], self.theme.background[3])

        # Surface = sdl2.sdlttf.TTF_RenderUTF8_Solid(self.font, text.encode(), color)
        surface = sdl2.sdlttf.TTF_RenderUTF8_LCD(self.font, text.encode(), color_fg, color_bg)  # pyright:ignore[reportUnknownMemberType, reportUnknownVariableType]
        texture = sdl2.SDL_CreateTextureFromSurface(self.renderer.sdlrenderer, surface)  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        rect = sdl2.SDL_Rect(x, y, surface.contents.w // self.font_mag, surface.contents.h // self.font_mag)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        sdl2.SDL_FreeSurface(surface)  # pyright: ignore[reportUnknownMemberType]
        sdl2.SDL_RenderCopy(self.renderer.sdlrenderer, texture, None, rect)  # pyright: ignore[reportUnknownMemberType]
        sdl2.SDL_DestroyTexture(texture)  # pyright: ignore[reportUnknownMemberType]
        return rect

    def render(self, frames:Frames):
        def _render(id:int, frames: Frames):
            idx: int | None = frames.idx(id)
            if idx is None:
                return
            frame = frames.frames[idx]
            rect = sdl2.SDL_Rect(frame.x, frame.y, frame.wx, frame.hy)
            if frame.id == frames.active_id:
                self.renderer.draw_rect(rect, color=self.theme.active_border)  # pyright: ignore[reportUnknownMemberType]
            else:
                self.renderer.draw_rect(rect, color=self.theme.border)  # pyright: ignore[reportUnknownMemberType]
            if frame.c_lu!=0 and frame.c_rd!=0:
                _render(frame.c_lu, frames)
                _render(frame.c_rd, frames)

        _render(frames.root_id, frames)


def run():
    # get path to script:
    script_path:str = os.path.dirname(os.path.abspath(__file__))
    # get path to font at ../Resources/IosevkaNerdFontMono-Regular.ttf
    font_path = os.path.join(script_path, "../Resources/IosevkaNerdFontMono-Regular.ttf")

    sdl2.ext.init()
    sdl2.sdlttf.TTF_Init()

    window = sdl2.ext.Window("Resizable Window", size=(800, 600), flags=(sdl2.SDL_WINDOW_RESIZABLE | sdl2.SDL_WINDOW_ALLOW_HIGHDPI |  sdl2.SDL_RENDERER_ACCELERATED))
    window.show()
    renderer = sdl2.ext.Renderer(window, flags=sdl2.SDL_RENDERER_ACCELERATED)

    frame_renderer = FrameRenderer(800, 600, renderer, font_path)

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
        events = sdl2.ext.get_events()  # pyright: ignore[reportUnknownVariableType]
        for event in events:  # pyright: ignore[reportUnknownVariableType]
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
                if key_name == '=':
                    frames.size(delta=0.02)
                    frames.geometry(0,0,wx, hy)
                    break
                if key_name == '-':
                    frames.size(delta= -0.02)
                    frames.geometry(0,0,wx, hy)
                    break 
                if key_name == 'C':
                    _ = frames.delete()
                    frames.geometry(0,0,wx, hy)
                    break

                else:
                    print(f"Key pressed: {key_name}")
            if event.type == sdl2.SDL_TEXTINPUT:  # pyright: ignore[reportUnknownMemberType]
                text_char:str = cast(str, event.text.text.decode('utf-8'))  # pyright: ignore[reportUnknownMemberType]
                text_type:int = cast(int, event.text.type)  # pyright: ignore[reportUnknownMemberType]
                print(f"Text {text_char}, type: {text_type}")

        renderer.clear((50, 50, 50))  # pyright: ignore[reportUnknownMemberType]
        frame_renderer.render(frames)
        renderer.present()
        sdl2.SDL_Delay(10)  # pyright: ignore[reportUnknownMemberType]

    sdl2.ext.quit()

if __name__ == "__main__":
    run()
