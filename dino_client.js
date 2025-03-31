const socket = new WebSocket("ws://localhost:8765");
let lastAction = "none";
let lastScore = 0;
let isJumping = false;

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

socket.onopen = () => {
  silenceSoundCrashes();
  maybeStartGame();
  sendGameState();
};

socket.onmessage = async (event) => {
  const { action } = JSON.parse(event.data);
  lastAction = action;
  await handleAction(action);
  sendGameState();
};

async function sendGameState() {
  await autoReplay();

  const gameObj = getGameState();
  if (!gameObj || socket.readyState !== WebSocket.OPEN) {
    await sleep(100);
    await sendGameState();
    return;
  }

  const crashed = Runner.instance_.crashed;
  let reward = 0;

  const distance = gameObj.state[0];
  const height = gameObj.state[1];
  const type = gameObj.state[2];  // 1 = bird

  if (crashed) {
    reward = -1000;
    console.log("🔥 Crashed at score:", Runner.instance_.distanceRan);
  } else {
    const currentScore = Runner.instance_.distanceRan || 0;
    reward = currentScore - lastScore;
    lastScore = currentScore;

    if (lastAction === "none") reward += 1;
    if (lastAction === "jump" && distance > 80) reward -= 100;
    reward += 0.5;

    // Bird-specific logic (yPos < 75 = high/mid)
    if (type === 1) {
      if (lastAction === "jump" && height < 75) {
        reward -= 500; // bad jump under high/mid bird
      } else if (lastAction === "none" && height < 75) {
        reward += 500; // correct behavior: ignore high/mid bird
      } else if (lastAction === "jump" && height >= 75) {
        reward += 500; // correct jump on low bird
      }
    }
  }

  reward = Math.max(Math.min(reward, 1000), -1000);

  // console.log("State:", gameObj.state, "Reward:", reward.toFixed(2), "Action:", lastAction);

  socket.send(JSON.stringify({
    state: gameObj.state,
    reward: reward,
    done: crashed
  }));
}

async function handleAction(action) {
  const runner = Runner.instance_;
  if (!runner || isJumping) return;

  if (action === "jump") {
    isJumping = true;
    const up = { keyCode: 38, preventDefault: () => {} };
    runner.onKeyDown(up);
    await sleep(100);
    runner.onKeyUp(up);
    await sleep(400); // cooldown
    isJumping = false;
  }
}

function getGameState() {
  const runner = Runner.instance_;
  const speed = runner.currentSpeed;
  const dinoX = 24;
  const obs = runner?.horizon?.obstacles[0];
  if (!obs) return { state: [999, 0, 0, speed] };

  const distance = obs.xPos - dinoX;
  const height = obs.yPos;
  const type = obs.typeConfig?.type === 'PTERODACTYL' ? 1 : 0;

  return { state: [distance, height, type, speed] };
}

function maybeStartGame() {
  const runner = Runner.instance_;
  if (!runner || runner.playing) return;
  const key = { keyCode: 32, preventDefault: () => {} };
  runner.onKeyDown(key);
  setTimeout(() => runner.onKeyUp(key), 300);
}

async function autoReplay() {
  const runner = Runner.instance_;
  if (!runner?.crashed) return;
  await sleep(700);
  const key = { keyCode: 32, preventDefault: () => {} };
  runner.onKeyDown(key);
  setTimeout(() => runner.onKeyUp(key), 300);
}

function silenceSoundCrashes() {
  if (typeof GeneratedSoundFx !== "undefined") {
    GeneratedSoundFx.prototype.background = function () {};
  }
}
