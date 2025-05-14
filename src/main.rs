extern crate sdl2;

use sdl2::event::Event;
use sdl2::keyboard::Keycode;
use sdl2::pixels::Color;
use sdl2::rect::Rect;
use std::time::Duration;

// Define a struct to store color theme information
#[derive(Debug, Clone)]
struct ColorTheme {
    background: Color,
    border_color: Color,
    active_frame_color: Color,
}

// Define a struct to represent a frame
#[derive(Debug, Clone)]
struct Frame {
    x: i32,
    y: i32,
    width: i32,
    height: i32,
}

impl Frame {
    // Check if a point is inside the frame
    fn _contains(&self, px: i32, py: i32) -> bool {
        px >= self.x
            && px < self.x + self.width
            && py >= self.y
            && py < self.y + self.height
    }
}

// Add direction enum after the Frame struct definition
#[derive(Debug, Clone, Copy)]
enum Direction {
    Up,
    Down,
    Left,
    Right,
}

// Define a struct to manage the list of frames
struct FrameManager {
    frames: Vec<Frame>,
    active_frame: usize,
    color_theme: ColorTheme,
    window_width: u32,
    window_height: u32,
}

impl FrameManager {
    fn new(window_width: u32, window_height: u32, color_theme: &ColorTheme) -> Self {
        Self {
            frames: vec![Frame {
                x: 0,
                y: 0,
                width: window_width as i32,
                height: window_height as i32,
            }],
            active_frame: 0,
            color_theme: color_theme.clone(),
            window_width,
            window_height,
        }
    }

    fn split_horizontal(&mut self) {
        if let Some(frame) = self.frames.get(self.active_frame).cloned() {
            let new_height = frame.height / 2;
            self.frames[self.active_frame].height = new_height;
            self.frames.push(Frame {
                x: frame.x,
                y: frame.y + new_height,
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
                x: frame.x + new_width,
                y: frame.y,
                width: new_width,
                height: frame.height,
            });
        }
    }

    // Close the active frame
    fn close_active_frame(&mut self) {
        if self.frames.len() <= 1 {
            return; // Don't close the last frame
        }

        // Get the frame to be closed
        let closed_frame = self.frames.remove(self.active_frame);

        // Find frames that are adjacent to the closed frame
        let mut adjacent_frames = Vec::new();

        for (idx, frame) in self.frames.iter().enumerate() {
            // Check if horizontally adjacent (left or right)
            let horizontally_adjacent = frame.y == closed_frame.y
                && frame.height == closed_frame.height
                && (frame.x + frame.width as i32 == closed_frame.x
                    || closed_frame.x + closed_frame.width as i32 == frame.x);

            // Check if vertically adjacent (above or below)
            let vertically_adjacent = frame.x == closed_frame.x
                && frame.width == closed_frame.width
                && (frame.y + frame.height as i32 == closed_frame.y
                    || closed_frame.y + closed_frame.height as i32 == frame.y);

            if horizontally_adjacent || vertically_adjacent {
                adjacent_frames.push((idx, horizontally_adjacent));
            }
        }

        // If we found adjacent frames, expand them to fill the space
        if !adjacent_frames.is_empty() {
            // Group by orientation
            let horizontal: Vec<_> = adjacent_frames
                .iter()
                .filter(|(_, is_horizontal)| *is_horizontal)
                .map(|(idx, _)| *idx)
                .collect();

            let vertical: Vec<_> = adjacent_frames
                .iter()
                .filter(|(_, is_horizontal)| !*is_horizontal)
                .map(|(idx, _)| *idx)
                .collect();

            if !horizontal.is_empty() {
                // Expand horizontally - fix type mismatches
                let space_per_frame = closed_frame.width / horizontal.len() as i32;
                let remaining_space = closed_frame.width % horizontal.len() as i32;

                for (i, &idx) in horizontal.iter().enumerate() {
                    let frame = &mut self.frames[idx];
                    let extra = if i == 0 { remaining_space } else { 0 };

                    if frame.x > closed_frame.x {
                        // Frame is to the right of closed frame
                        frame.x -= space_per_frame;
                        if i == 0 {
                            frame.x -= remaining_space;
                        }
                    }
                    frame.width += space_per_frame + extra;
                }
            } else if !vertical.is_empty() {
                // Expand vertically - fix type mismatches
                let space_per_frame = closed_frame.height / vertical.len() as i32;
                let remaining_space = closed_frame.height % vertical.len() as i32;

                for (i, &idx) in vertical.iter().enumerate() {
                    let frame = &mut self.frames[idx];
                    let extra = if i == 0 { remaining_space } else { 0 };

                    if frame.y > closed_frame.y {
                        // Frame is below the closed frame
                        frame.y -= space_per_frame;
                        if i == 0 {
                            frame.y -= remaining_space;
                        }
                    }
                    frame.height += space_per_frame + extra;
                }
            }
        } else {
            // If no adjacent frames section - fix type mismatches
            if !self.frames.is_empty() {
                let mut nearest_idx = 0;
                let mut min_distance = f32::MAX;

                for (idx, frame) in self.frames.iter().enumerate() {
                    let dx = (frame.x + frame.width as i32 / 2)
                        - (closed_frame.x + closed_frame.width as i32 / 2);
                    let dy = (frame.y + frame.height as i32 / 2)
                        - (closed_frame.y + closed_frame.height as i32 / 2);
                    let distance = (dx * dx + dy * dy) as f32;

                    if distance < min_distance {
                        min_distance = distance;
                        nearest_idx = idx;
                    }
                }

                // Expand the nearest frame to cover the closed frame
                let frame = &mut self.frames[nearest_idx];
                let min_x = frame.x.min(closed_frame.x);
                let min_y = frame.y.min(closed_frame.y);
                let max_x = 
                    (frame.x + frame.width).max(closed_frame.x + closed_frame.width);
                let max_y = 
                    (frame.y + frame.height).max(closed_frame.y + closed_frame.height);

                frame.x = min_x;
                frame.y = min_y;
                frame.width = max_x - min_x;
                frame.height = max_y - min_y;
            }
        }

        // Make sure we don't have any gaps
        self.adjust_frames_to_window(self.window_width, self.window_height);

        // Update active frame index
        self.active_frame = self.active_frame.min(self.frames.len() - 1);
    }

    // Delete all other frames except the active one
    fn delete_other_frames(&mut self) {
        // Keep only the active frame and resize it to fill the window
        self.frames = vec![Frame {
            x: 0,
            y: 0,
            width: self.window_width as i32,
            height: self.window_height as i32,
        }];
        self.active_frame = 0;
    }

    // Resize the active frame
    fn resize_active_frame(&mut self, dx: i32, dy: i32) {
        if self.frames.len() <= 1 || (dx == 0 && dy == 0) {
            return; // No need to resize when there's only one frame or no change
        }

        if let Some(active_frame) = self.frames.get(self.active_frame).cloned() {
            let min_size = 50; // Minimum allowed frame size

            // Find affected frames
            let mut affected_right_frames = Vec::new();
            let mut affected_bottom_frames = Vec::new();

            // Find frames adjacent to the active frame
            for (idx, frame) in self.frames.iter().enumerate() {
                if idx == self.active_frame {
                    continue;
                }

                // Check if frame is to the right and has vertical overlap
                if frame.x == active_frame.x + active_frame.width {
                    let overlap = (frame.y + frame.height).min(active_frame.y + active_frame.height)
                        - frame.y.max(active_frame.y);
                    if overlap > 0 {
                        affected_right_frames.push(idx);
                    }
                }

                // Check if frame is below and has horizontal overlap
                if frame.y == active_frame.y + active_frame.height {
                    let overlap = (frame.x + frame.width).min(active_frame.x + active_frame.width)
                        - frame.x.max(active_frame.x);
                    if overlap > 0 {
                        affected_bottom_frames.push(idx);
                    }
                }
            }

            // Apply horizontal resize if possible
            if dx != 0 && active_frame.width + dx >= min_size &&
               affected_right_frames.iter().all(|&idx| self.frames[idx].width - dx >= min_size) {
                // Resize active frame
                self.frames[self.active_frame].width = active_frame.width + dx;

                // Adjust frames to the right
                for &idx in &affected_right_frames {
                    let frame = &mut self.frames[idx];
                    frame.x += dx;
                    frame.width -= dx;
                }
            }

            // Apply vertical resize if possible
            if dy != 0 && active_frame.height + dy >= min_size &&
               affected_bottom_frames.iter().all(|&idx| self.frames[idx].height - dy >= min_size) {
                // Resize active frame
                self.frames[self.active_frame].height = active_frame.height + dy;

                // Adjust frames below
                for &idx in &affected_bottom_frames {
                    let frame = &mut self.frames[idx];
                    frame.y += dy;
                    frame.height -= dy;
                }
            }

            // Ensure window is fully covered
            self.adjust_frames_to_window(self.window_width, self.window_height);
        }
    }

    // Resize all frames when window size changes
    fn resize_window(&mut self, new_width: u32, new_height: u32) {
        let width_ratio = new_width as f32 / self.window_width as f32;
        let height_ratio = new_height as f32 / self.window_height as f32;

        // Resize all frames proportionally
        for frame in &mut self.frames {
            frame.x = (frame.x as f32 * width_ratio) as i32;
            frame.y = (frame.y as f32 * height_ratio) as i32;
            frame.width = (frame.width as f32 * width_ratio) as i32;
            frame.height = (frame.height as f32 * height_ratio) as i32;
        }

        // Ensure frames exactly cover the window after resize
        self.adjust_frames_to_window(new_width, new_height);

        // Update stored window dimensions
        self.window_width = new_width;
        self.window_height = new_height;
    }

    // Improved method to adjust frames after resize
    fn adjust_frames_to_window(&mut self, width: u32, height: u32) {
        if self.frames.is_empty() {
            return;
        }
        
        let width_i32 = width as i32;
        let height_i32 = height as i32;
        
        // Step 1: Find frames at window edges
        let mut right_edge_frames = Vec::new();
        let mut bottom_edge_frames = Vec::new();
        
        // Find the right-most and bottom-most positions
        let mut max_right = 0;
        let mut max_bottom = 0;
        
        for frame in &self.frames {
            let right_edge = frame.x + frame.width;
            let bottom_edge = frame.y + frame.height;
            
            if right_edge > max_right {
                max_right = right_edge;
                right_edge_frames.clear();
                right_edge_frames.push(frame.x);
            } else if right_edge == max_right {
                right_edge_frames.push(frame.x);
            }
            
            if bottom_edge > max_bottom {
                max_bottom = bottom_edge;
                bottom_edge_frames.clear();
                bottom_edge_frames.push(frame.y);
            } else if bottom_edge == max_bottom {
                bottom_edge_frames.push(frame.y);
            }
        }
        
        // Step 2: Fix horizontal gaps - extend frames to the right edge of window
        for frame in &mut self.frames {
            let right_edge = frame.x + frame.width;
            if right_edge == max_right && right_edge < width_i32 {
                // Extend this frame to the right edge of window
                frame.width = width_i32 - frame.x;
            }
        }
        
        // Step 3: Fix vertical gaps - extend frames to the bottom edge of window
        for frame in &mut self.frames {
            let bottom_edge = frame.y + frame.height;
            if bottom_edge == max_bottom && bottom_edge < height_i32 {
                // Extend this frame to the bottom edge of window
                frame.height = height_i32 - frame.y;
            }
        }
        
        // Step 4: Check for and fix any remaining gaps
        let mut has_gaps = true;
        while has_gaps {
            has_gaps = false;
            
            // Check if any frame can be extended horizontally
            for i in 0..self.frames.len() {
                let frame = &self.frames[i];
                let right_edge = frame.x + frame.width;
                
                // If this frame doesn't reach the window edge, find a frame to its right
                if right_edge < width_i32 {
                    let mut found_neighbor = false;
                    
                    for j in 0..self.frames.len() {
                        if i == j { continue; }
                        let other = &self.frames[j];
                        
                        // Check if other frame is to the right of this one
                        if other.x == right_edge && 
                           ((other.y <= frame.y && other.y + other.height > frame.y) ||
                            (frame.y <= other.y && frame.y + frame.height > other.y)) {
                            found_neighbor = true;
                            break;
                        }
                    }
                    
                    if !found_neighbor {
                        // No frame to the right - extend this one
                        self.frames[i].width = width_i32 - frame.x;
                        has_gaps = true;
                        break;
                    }
                }
            }
            
            // Check if any frame can be extended vertically
            for i in 0..self.frames.len() {
                let frame = &self.frames[i];
                let bottom_edge = frame.y + frame.height;
                
                // If this frame doesn't reach the window edge, find a frame below it
                if bottom_edge < height_i32 {
                    let mut found_neighbor = false;
                    
                    for j in 0..self.frames.len() {
                        if i == j { continue; }
                        let other = &self.frames[j];
                        
                        // Check if other frame is below this one
                        if other.y == bottom_edge && 
                           ((other.x <= frame.x && other.x + other.width > frame.x) ||
                            (frame.x <= other.x && frame.x + frame.width > other.x)) {
                            found_neighbor = true;
                            break;
                        }
                    }
                    
                    if !found_neighbor {
                        // No frame below - extend this one
                        self.frames[i].height = height_i32 - frame.y;
                        has_gaps = true;
                        break;
                    }
                }
            }
        }
    }

    // Draw all frames and borders
    fn draw(&self, canvas: &mut sdl2::render::Canvas<sdl2::video::Window>) {
        for (i, frame) in self.frames.iter().enumerate() {
            // Draw frame background
            canvas.set_draw_color(self.color_theme.background);
            canvas
                .fill_rect(Rect::new(frame.x, frame.y, frame.width as u32, frame.height as u32))
                .unwrap();

            // Set border color based on whether this is the active frame
            if i == self.active_frame {
                canvas.set_draw_color(self.color_theme.active_frame_color);
            } else {
                canvas.set_draw_color(self.color_theme.border_color);
            }
            
            // Draw border
            canvas
                .draw_rect(Rect::new(frame.x, frame.y, frame.width as u32, frame.height as u32))
                .unwrap();
        }
    }

    // Improved frame selection method
    fn select_frame_in_direction(&mut self, direction: Direction) {
        if self.frames.len() <= 1 {
            return; // Nothing to select if there's only one frame
        }
        
        let active_frame = &self.frames[self.active_frame];
        
        // Calculate center points and edges of active frame
        let active_center_x = active_frame.x + active_frame.width as i32 / 2;
        let active_center_y = active_frame.y + active_frame.height as i32 / 2;
        let active_left = active_frame.x;
        let active_right = active_frame.x + active_frame.width as i32;
        let active_top = active_frame.y;
        let active_bottom = active_frame.y + active_frame.height as i32;
        
        // Variables to track the best frame to select
        let mut best_idx = None;
        let mut best_score = std::f32::MAX;
        
        for (idx, frame) in self.frames.iter().enumerate() {
            if idx == self.active_frame {
                continue; // Skip the active frame
            }
            
            let frame_center_x = frame.x + frame.width as i32 / 2;
            let frame_center_y = frame.y + frame.height as i32 / 2;
            let frame_left = frame.x;
            let frame_right = frame.x + frame.width as i32;
            let frame_top = frame.y;
            let frame_bottom = frame.y + frame.height as i32;
            
            // Check if frame is in the specified direction
            let is_in_direction = match direction {
                Direction::Up => frame_bottom <= active_top, // Frame is above
                Direction::Down => frame_top >= active_bottom, // Frame is below
                Direction::Left => frame_right <= active_left, // Frame is to the left
                Direction::Right => frame_left >= active_right, // Frame is to the right
            };
            
            if !is_in_direction {
                continue;
            }
            
            // Calculate distance and alignment score
            let dx = (frame_center_x - active_center_x).abs() as f32;
            let dy = (frame_center_y - active_center_y).abs() as f32;
            
            // Calculate horizontal/vertical overlap
            let horizontal_overlap = (active_right.min(frame_right) - active_left.max(frame_left)).max(0) as f32;
            let vertical_overlap = (active_bottom.min(frame_bottom) - active_top.max(frame_top)).max(0) as f32;
            
            // Different scoring based on direction
            let score = match direction {
                Direction::Left | Direction::Right => {
                    // Prioritize frames with vertical overlap and closer horizontal distance
                    if vertical_overlap > 0.0 {
                        dx - vertical_overlap * 0.5
                    } else {
                        dx + dy
                    }
                },
                Direction::Up | Direction::Down => {
                    // Prioritize frames with horizontal overlap and closer vertical distance
                    if horizontal_overlap > 0.0 {
                        dy - horizontal_overlap * 0.5
                    } else {
                        dy + dx
                    }
                }
            };
            
            if score < best_score {
                best_score = score;
                best_idx = Some(idx);
            }
        }
        
        // Update active frame if a suitable frame was found
        if let Some(idx) = best_idx {
            self.active_frame = idx;
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
        .resizable() // Add resizable flag
        .build()
        .map_err(|e| e.to_string())?;

    // Create a canvas to draw on
    let mut canvas = window.into_canvas().build().map_err(|e| e.to_string())?;

    // Define a color theme
    let theme = ColorTheme {
        background: Color::RGB(20, 20, 50),
        border_color: Color::RGB(0, 0, 255),
        active_frame_color: Color::RGB(255, 128, 128),
    };

    // Event loop
    let mut event_pump = sdl_context.event_pump()?;

    // Initialize frame manager
    let mut frame_manager = FrameManager::new(800, 600, &theme);
    
    // Event loop variables
    let mut resizing = false;
    let mut resize_dx = 0;
    let mut resize_dy = 0;
    let mut x_just_released = false;  // Add this variable to track X key release

    'running: loop {
        for event in event_pump.poll_iter() {
            match event {
                Event::Quit { .. } => break 'running,
                Event::Window {
                    win_event: sdl2::event::WindowEvent::Resized(width, height),
                    ..
                } => {
                    frame_manager.resize_window(width as u32, height as u32);
                },
                Event::KeyDown {
                    keycode: Some(Keycode::X),
                    ..
                } => resizing = true,
                Event::KeyUp {
                    keycode: Some(Keycode::X),
                    ..
                } => {
                    resizing = false;
                    x_just_released = true; // Mark that X was just released
                },
                Event::KeyDown {
                    keycode: Some(Keycode::Up),
                    ..
                } => {
                    if x_just_released {
                        // Select frame above the current one
                        frame_manager.select_frame_in_direction(Direction::Up);
                        x_just_released = false;
                    } else if resizing {
                        resize_dy -= 10;
                    }
                },
                Event::KeyDown {
                    keycode: Some(Keycode::Down),
                    ..
                } => {
                    if x_just_released {
                        // Select frame below the current one
                        frame_manager.select_frame_in_direction(Direction::Down);
                        x_just_released = false;
                    } else if resizing {
                        resize_dy += 10;
                    }
                },
                Event::KeyDown {
                    keycode: Some(Keycode::Left),
                    ..
                } => {
                    if x_just_released {
                        // Select frame to the left of the current one
                        frame_manager.select_frame_in_direction(Direction::Left);
                        x_just_released = false;
                    } else if resizing {
                        resize_dx -= 10;
                    }
                },
                Event::KeyDown {
                    keycode: Some(Keycode::Right),
                    ..
                } => {
                    if x_just_released {
                        // Select frame to the right of the current one
                        frame_manager.select_frame_in_direction(Direction::Right);
                        x_just_released = false;
                    } else if resizing {
                        resize_dx += 10;
                    }
                },
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
                _ => {
                    // Reset x_just_released if any other key is pressed
                    x_just_released = false;
                }
            }
        }

        if resizing {
            frame_manager.resize_active_frame(resize_dx, resize_dy);
            resize_dx = 0;
            resize_dy = 0;
        }

        // Draw frames
        canvas.set_draw_color(theme.background); // Clear screen
        canvas.clear();
        frame_manager.draw(&mut canvas);
        canvas.present();

        // Sleep to limit CPU usage
        std::thread::sleep(Duration::from_millis(16));
    }

    Ok(())
}
