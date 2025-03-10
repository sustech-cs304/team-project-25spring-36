# Intelligent VScode Extension Proposal

## 施米乐 王宇航 王玺华 范升泰 王梓鑫

## Functional Requirements

#### 1. **Intuitive Course Resource Management**

- **For Students:**
   Log in and dive into your courses! Instantly access all your enrolled class materials—notes, videos, and more—right at your fingertips, neatly organized and ready to explore.
- **For Teachers:**
   Sign in and take control! Easily assign courses to students, upload fresh materials like slides or videos, and share coding challenges with just a tap—teaching made simple and fun.

#### 2. **In-Text Code Execution**

- Code on the go with our sleek, built-in notebook! Write and run Python (or more) directly in your lessons, just like a pro. Test your skills with preset answers—see if your code nails it every time.

#### 3. **Collaborative Coding in Real-Time**

- Team up and code together! Work on the same file with friends or classmates in real time, chat as you go, and share your creations effortlessly—learning is better with a crew.

#### 4. **AI Learning Assistant**

- Meet your smart study buddy! Ask anything about your courses and get instant answers, quick summaries, or highlights of key material—all powered by cutting-edge AI to keep you ahead.

#### 5. **Course Progress Tracking**

- Stay on top of your game! Track your progress with a glance—see completed assignments, check off materials, and never miss a deadline. Teachers can peek at how everyone’s doing, too!


## Non-functional Requirements

### Usability

**How We Make It Happen:**
 Our platform is designed for effortless vibes! Students and teachers will love the clean, simple layout—jump into courses with a tap, upload files with a drag, and find everything exactly where it should be. Whether you’re coding or browsing lessons, it’s so easy you’ll feel like a pro from day one. We’ll fine-tune it with real users to keep it smooth for everyone.

### Performance

**How We Stay Snappy:**
 Speed is our superpower! From running code to chatting with your crew, everything loads fast and flows without a hitch. Collaborate in real time, watch videos, or tackle big assignments—no lag, no fuss. We’re built to keep up with your busiest study days, every time.

### Security

**How We Lock It Down:**
 Your trust is everything to us! With rock-solid security, we’ve got your logins, files, and chats on lockdown—think strong passwords, private connections, and zero leaks. Teachers can share materials worry-free, and students can focus on learning, knowing their work stays safe and sound in our digital vault.

## Data Requirements

### Course Material

- Stores course content (in our custom data type) for teacher uploads and student access, organized by course.

### User Registration by Email

- Requires email for user account creation and authentication.

## Technical Requirements

### Backend

- Docker: Ensures cross-platform compatibility.
- Postgres: Manages data storage for courses and users.
- Python 3.10: Powers backend logic and functionality.

### Front-end

- VS Code: Used for development environment.
- Node.js & npm: Drives front-end interface and features.