const board = document.getElementById("board");
const ctx = board.getContext("2d");

const scoreEl = document.getElementById("score");
const bestEl = document.getElementById("best");
const overlay = document.getElementById("overlay");
const overlayTitle = document.getElementById("overlay-title");
const overlayText = document.getElementById("overlay-text");

const startBtn = document.getElementById("start-btn");
const pauseBtn = document.getElementById("pause-btn");
const restartBtn = document.getElementById("restart-btn");

const GRID = 20;
const TILE = board.width / GRID;
const SPEED_MS = 120;

let snake;
let direction;
let queuedDirection;
let food;
let score;
let bestScore = Number(localStorage.getItem("snake_best") || 0);
let isRunning = false;
let isPaused = false;
let timer = null;

bestEl.textContent = String(bestScore);

function initGame() {
  snake = [
    { x: 10, y: 10 },
    { x: 9, y: 10 },
    { x: 8, y: 10 },
  ];
  direction = "right";
  queuedDirection = "right";
  score = 0;
  scoreEl.textContent = "0";
  spawnFood();
  draw();
}

function spawnFood() {
  let newFood;
  do {
    newFood = {
      x: Math.floor(Math.random() * GRID),
      y: Math.floor(Math.random() * GRID),
    };
  } while (snake.some((part) => part.x === newFood.x && part.y === newFood.y));
  food = newFood;
}

function setOverlay(title, text, show = true) {
  overlayTitle.textContent = title;
  overlayText.textContent = text;
  overlay.classList.toggle("show", show);
}

function startGame() {
  if (isRunning && !isPaused) {
    return;
  }

  if (!isRunning) {
    initGame();
    isRunning = true;
  }

  isPaused = false;
  pauseBtn.textContent = "Pause";
  setOverlay("", "", false);
  clearInterval(timer);
  timer = setInterval(tick, SPEED_MS);
}

function pauseGame() {
  if (!isRunning) {
    return;
  }

  isPaused = !isPaused;
  if (isPaused) {
    clearInterval(timer);
    pauseBtn.textContent = "Resume";
    setOverlay("Paused", "Press Space or tap Resume.");
  } else {
    pauseBtn.textContent = "Pause";
    setOverlay("", "", false);
    timer = setInterval(tick, SPEED_MS);
  }
}

function restartGame() {
  clearInterval(timer);
  isRunning = false;
  isPaused = false;
  pauseBtn.textContent = "Pause";
  initGame();
  setOverlay("Ready?", "Press Space or tap Start to play.");
}

function gameOver() {
  clearInterval(timer);
  isRunning = false;
  isPaused = false;
  pauseBtn.textContent = "Pause";

  if (score > bestScore) {
    bestScore = score;
    bestEl.textContent = String(bestScore);
    localStorage.setItem("snake_best", String(bestScore));
  }

  setOverlay("Game Over", "Press Start or Restart for a new run.");
}

function setDirection(next) {
  const opposite = {
    up: "down",
    down: "up",
    left: "right",
    right: "left",
  };

  if (opposite[direction] === next) {
    return;
  }

  queuedDirection = next;
}

function tick() {
  direction = queuedDirection;

  const head = { ...snake[0] };
  if (direction === "up") head.y -= 1;
  if (direction === "down") head.y += 1;
  if (direction === "left") head.x -= 1;
  if (direction === "right") head.x += 1;

  const hitWall = head.x < 0 || head.x >= GRID || head.y < 0 || head.y >= GRID;
  const hitSelf = snake.some((part) => part.x === head.x && part.y === head.y);

  if (hitWall || hitSelf) {
    gameOver();
    return;
  }

  snake.unshift(head);

  if (head.x === food.x && head.y === food.y) {
    score += 10;
    scoreEl.textContent = String(score);
    spawnFood();
  } else {
    snake.pop();
  }

  draw();
}

function draw() {
  ctx.clearRect(0, 0, board.width, board.height);

  for (let i = 0; i < snake.length; i += 1) {
    const part = snake[i];
    ctx.fillStyle = i === 0 ? "#42f59e" : "#1ed67a";
    ctx.fillRect(part.x * TILE + 1, part.y * TILE + 1, TILE - 2, TILE - 2);
  }

  ctx.fillStyle = "#ff5c5c";
  ctx.beginPath();
  ctx.arc(
    food.x * TILE + TILE / 2,
    food.y * TILE + TILE / 2,
    TILE / 2.6,
    0,
    Math.PI * 2
  );
  ctx.fill();
}

document.addEventListener("keydown", (event) => {
  const key = event.key.toLowerCase();

  if (key === "arrowup" || key === "w") setDirection("up");
  if (key === "arrowdown" || key === "s") setDirection("down");
  if (key === "arrowleft" || key === "a") setDirection("left");
  if (key === "arrowright" || key === "d") setDirection("right");

  if (key === " ") {
    event.preventDefault();
    if (!isRunning) {
      startGame();
    } else {
      pauseGame();
    }
  }
});

startBtn.addEventListener("click", startGame);
pauseBtn.addEventListener("click", pauseGame);
restartBtn.addEventListener("click", restartGame);

document.querySelectorAll(".dir").forEach((button) => {
  button.addEventListener("click", () => {
    setDirection(button.dataset.dir);
    if (!isRunning) {
      startGame();
    }
  });
});

restartGame();
