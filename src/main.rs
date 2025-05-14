extern crate sdl2;

use sdl2::pixels::Color;
use sdl2::event::Event;
use sdl2::keyboard::Keycode;
use sdl2::rect::Rect;
use std::time::Duration;

// Define a struct to store color theme information
struct ColorTheme {
    background: Color,
    draw_color: Color,
    border_color: Color,
}

// Define a struct to represent a frame
#[derive(Debug, Clone)]
struct Frame {
    x: i32,
    y: i32,
    width: u32,
    height: u32,
}

impl Frame {
    // Check if a point is inside the frame
    fn contains(&self, px: i32, py: i32) -> bool {
        px >= self.x && px < self.x + self.width as i32 && py >= self.y && py < self.y + self.height as i32
    }
}

// Define a struct to manage the list of frames
struct FrameManager {
    frames: Vec<Frame>,
    active_frame: usize,
    color_theme: ColorTheme,
}

impl FrameManager {
    fn new(window_width: u32, window_height: u32, color_theme: ColorTheme) -> Self {
        Self {
            frames: vec![Frame {
                x: 0,
                y: 0,
                width: window_width,
                height: window_height,
            }],
            active_frame: 0,
            color_theme,
        }
    }

    // Split the active frame horizontally
    fn split_horizontal(&mut self) {
        if let Some(frame) = self.frames.get(self.active_frame).cloned() {
            let new_height = frame.height / 2;
            self.frames[self.active_frame].height = new_height;
            self.frames.push(Frame {
                x: frame.x,
                y: frame.y + new_height as i32,
                width: frame.width,
                height: new_height,
            });
        }
    }

    // Split the active frame vertically
    fn split_vertical(&mut self) {
        if let Some(frame) = self.frames.get(self.active_frame).cloned() {
            let new_width = frame.width / 2;
            self.frames[self.active_frame].width = new_width;
            self.frames.push(Frame {
                x: frame.x + new_width as i32,
                y: frame.y,
                width: new_width,
                height: frame.height,
            });
        }
    }

    // Close the active frame
    fn close_active_frame(&mut self) {
        if self.frames.len() > 1 {
            self.frames.remove(self.active_frame);
            self.active_frame = self.active_frame.saturating_sub(1);
        }
    }

    // Delete all other frames except the active one
    fn delete_other_frames(&mut self) {
        if let Some(active_frame) = self.frames.get(self.active_frame).cloned() {
            self.frames = vec![active_frame];
            self.active_frame = 0;
        }
    }

    // Resize the active frame
    fn resize_active_frame(&mut self, dx: i32, dy: i32) {
        if let Some(frame) = self.frames.get_mut(self.active_frame) {
            frame.width = (frame.width as i32 + dx).max(10) as u32;
            frame.height = (frame.height as i32 + dy).max(10) as u32;
        }
    }

    // Draw all frames and borders
    fn draw(&self, canvas: &mut sdl2::render::Canvas<sdl2::video::Window>) {
        for frame in &self.frames {
            canvas.set_draw_color(self.color_theme.background); // Background color
            canvas.fill_rect(Rect::new(frame.x, frame.y, frame.width, frame.height)).unwrap();

            // Draw border
            canvas.set_draw_color(self.color_theme.border_color); // Border color
            canvas.draw_rect(Rect::new(frame.x, frame.y, frame.width, frame.height)).unwrap();
        }
    }
}

fn main() -> Result<(), String> {
    // Initialize the SDL2 context
    let sdl_context = sdl2::init()?;
    let video_subsystem = sdl_context.video()?;

    // Create a window
    let window = video_subsystem
        .window("SDL2 Window", 800, 600)
        .position_centered()
        .opengl()
        .build()
        .map_err(|e| e.to_string())?;

    // Create a canvas to draw on
    let mut canvas = window.into_canvas().build().map_err(|e| e.to_string())?;

    // Define a color theme
    let theme = ColorTheme {
        background: Color::RGB(20, 20, 50),
        draw_color: Color::RGB(200, 80, 80),
        border_color: Color::RGB(0, 0, 255),
    };

    // Event loop
    let mut event_pump = sdl_context.event_pump()?;

    // Initialize frame manager
    let mut frame_manager = FrameManager::new(800, 600, theme);

    // Event loop
    let mut resizing = false;
    let mut resize_dx = 0;
    let mut resize_dy = 0;

    'running: loop {
        for event in event_pump.poll_iter() {
            match event {
                Event::Quit { .. } => break 'running,
                Event::KeyDown {
                    keycode: Some(Keycode::X),
                    ..
                } => resizing = true,
                Event::KeyUp {
                    keycode: Some(Keycode::X),
                    ..
                } => resizing = false,
                Event::KeyDown {
                    keycode: Some(Keycode::Num2),
                    ..
                } => frame_manager.split_horizontal(),
                Event::KeyDown {
                    keycode: Some(Keycode::Num3),
                    ..
                } => frame_manager.split_vertical(),
                Event::KeyDown {
                    keycode: Some(Keycode::Num0),
                    ..
                } => frame_manager.close_active_frame(),
                Event::KeyDown {
                    keycode: Some(Keycode::Num1),
                    ..
                } => frame_manager.delete_other_frames(),
                Event::KeyDown {
                    keycode: Some(Keycode::Up),
                    ..
                } if resizing => resize_dy -= 10,
                Event::KeyDown {
                    keycode: Some(Keycode::Down),
                    ..
                } if resizing => resize_dy += 10,
                Event::KeyDown {
                    keycode: Some(Keycode::Left),
                    ..
                } if resizing => resize_dx -= 10,
                Event::KeyDown {
                    keycode: Some(Keycode::Right),
                    ..
                } if resizing => resize_dx += 10,
                _ => {}
            }
        }

        if resizing {
            frame_manager.resize_active_frame(resize_dx, resize_dy);
            resize_dx = 0;
            resize_dy = 0;
        }

        // Draw frames
        canvas.set_draw_color(Color::RGB(0, 0, 0)); // Clear screen
        canvas.clear();
        frame_manager.draw(&mut canvas);
        canvas.present();

        // Sleep to limit CPU usage
        std::thread::sleep(Duration::from_millis(16));
    }

    Ok(())
}

