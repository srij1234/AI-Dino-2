# 🦖 Chrome Dino RL Agent

This project trains a Reinforcement Learning (REINFORCE) agent to play the **Chrome Dino game** using only game state data — no screenshots or computer vision.

---

## 🚀 Features

- Uses a **policy gradient (REINFORCE)** algorithm
- Learns directly from:
  - Obstacle distance
  - Obstacle height
  - Obstacle type (cactus or PTERODACTYL)
  - Game speed
- Handles **high-flying PTERODACTYLs** intelligently
- Achieves scores well above **500+** with training
- WebSocket connection between browser JS and Python backend

---

## 🧠 State Representation

Agent receives a 4D vector each frame:
```
[state] = [distance_to_obstacle, obstacle_y_pos, obstacle_type, speed]
```
- `obstacle_type`: 0 = cactus, 1 = bird  
- `obstacle_y_pos`: lower value means higher-flying bird

---

## 🎡 Actions

Two discrete actions:
- `"none"` – do nothing
- `"jump"` – perform jump (no ducking supported yet)

---

## 🧠 How It Works

1. The JS code runs inside the Dino browser page.
2. It sends game state to a Python backend via WebSocket.
3. The backend chooses an action using the current policy.
4. JS executes the action and sends back the result + reward.
5. REINFORCE updates happen on episode end.

---

## ⚒️ Setup

### 1. Clone this repo
```bash
git clone https://github.com/your-username/dino-rl-agent.git
cd dino-rl-agent
```

### 2. Install Python deps
```bash
pip install tensorflow numpy websockets
```

### 3. Open Chrome Dino game (turn off internet, or visit: `chrome://dino`)

### 4. Inject `test.js` using browser dev console:
```javascript
// Paste contents of test.js into console and hit enter
```

### 5. Run backend
```bash
python test.py
```

---

## 🔪 Training Tips

- Let the model train for **100–300 episodes** for solid performance
- `dino_reinforce.weights.h5` will auto-save between episodes
- Forcing correct behavior for high flyers is implemented early in training

---

## 👑 Author

Built with frustration, persistence, and love.  
Train your Dino, and let it conquer the desert 🏜️

