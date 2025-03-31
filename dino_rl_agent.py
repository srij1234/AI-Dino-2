import os
import json
import asyncio
import numpy as np
import tensorflow as tf
import websockets

STATE_DIM = 4  # [distance, height, type, speed]
ACTIONS_LIST = ["none", "jump"]
NUM_ACTIONS = len(ACTIONS_LIST)
WEIGHTS_PATH = "dino_reinforce.weights.h5"

states, actions, rewards = [], [], []
episode_count = 0

model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(STATE_DIM,)),
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.Dense(NUM_ACTIONS, activation='softmax',
                          bias_initializer=tf.keras.initializers.Constant([2.0, -2.0]))  # favor "none"
])
optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)

if os.path.exists(WEIGHTS_PATH):
    model.load_weights(WEIGHTS_PATH)
    print("✅ Loaded weights")
else:
    print("🚫 No weights found. Training from scratch.")

def discount_rewards(rewards, gamma=0.99):
    discounted = np.zeros_like(rewards, dtype=np.float32)
    running_add = 0
    for t in reversed(range(len(rewards))):
        running_add = running_add * gamma + rewards[t]
        discounted[t] = running_add
    discounted = (discounted - np.mean(discounted)) / (np.std(discounted) + 1e-8)
    return discounted

async def handler(websocket, _):
    global states, actions, rewards, episode_count

    async for msg in websocket:
        data = json.loads(msg)
        state = np.array(data["state"], dtype=np.float32)
        reward = float(data["reward"]) / 1000.0  # normalize big rewards
        done = data["done"]

        state = np.expand_dims(state, axis=0)
        probs = model(state).numpy()[0]
        action_idx = np.random.choice(NUM_ACTIONS, p=probs)

        # ✅ Expert override during early training (for high flyer)
        # Uncomment if your dino isnt learning to jump/ignore given obstacle
        # distance, height, type_, speed = state[0]
        # if type_ == 1 and height < 75:
        #     action_idx = 0  # force "none"
        # elif type_==1  and distance+24<speed*18:
        #     action_idx = 1
        # print(f"Ep {episode_count} | Probs: {probs} | Action: {ACTIONS_LIST[action_idx]}")

        states.append(state[0])
        actions.append(action_idx)
        rewards.append(reward)

        await websocket.send(json.dumps({"action": ACTIONS_LIST[action_idx]}))

        if done:
            if len(states) < 2:
                states.clear()
                actions.clear()
                rewards.clear()
                continue

            discounted = discount_rewards(rewards)

            states_np = np.vstack(states)
            actions_np = np.array(actions)
            discounted_np = np.array(discounted)

            with tf.GradientTape() as tape:
                logits = model(states_np)
                action_masks = tf.one_hot(actions_np, NUM_ACTIONS)
                log_probs = tf.reduce_sum(action_masks * tf.math.log(logits + 1e-10), axis=1)
                loss = -tf.reduce_mean(log_probs * discounted_np)

            grads = tape.gradient(loss, model.trainable_variables)
            optimizer.apply_gradients(zip(grads, model.trainable_variables))

            print(f"🏁 Episode {episode_count} | Total reward: {sum(rewards)*1000:.1f}")
            model.save_weights(WEIGHTS_PATH)

            states.clear()
            actions.clear()
            rewards.clear()
            episode_count += 1

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("🚀 Dino REINFORCE server ready at ws://localhost:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
