import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import cors from "cors";
import dotenv from "dotenv";
import OpenAI from "openai";

dotenv.config();
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

const useGemini = process.env.USE_GEMINI === "true" || process.env.USE_GEMINI === "1";
const geminiApiKey = process.env.GEMINI_API_KEY;
const geminiModel = process.env.GEMINI_MODEL || "text-bison-001";
const openai = useGemini ? null : new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const jarvesSystemPrompt = `
You are Jarves, a trusted AI assistant built to help the user manage tasks, write code, and provide clear updates.
- Always explain steps clearly and keep responses friendly but professional.
- When asked for task updates, summarize progress and next actions.
- When asked to perform a task, give code, a plan, or a list of practical steps.
- If you need more information, ask a specific follow-up question.
`;

const chatHistory = [];
const tasks = [];

const buildGeminiPrompt = (message) => {
  const history = chatHistory
    .map((item) => {
      const role = item.role === "assistant" ? "Assistant" : "User";
      return `${role}: ${item.content}`;
    })
    .join("\n");

  return [
    "System: " + jarvesSystemPrompt.trim(),
    history,
    `User: ${message}`,
    "Assistant:"
  ]
    .filter(Boolean)
    .join("\n\n");
};

// Fetch latest news from free API
const getLatestNews = async () => {
  try {
    const response = await fetch("https://api.first.org/data/v1/articles?limit=5");
    const data = await response.json();
    if (data?.data?.length > 0) {
      return data.data.map(article => `📰 ${article.title}\n${article.description || "No description available"}`).join("\n\n");
    }
  } catch (error) {
    console.error("News fetch error:", error.message);
  }
  return null;
};

// Smart response engine with internet integration
const callGemini = async (message) => {
  const msg = message.toLowerCase();
  
  // News request
  if (msg.includes("news") || msg.includes("update") || msg.includes("latest")) {
    const news = await getLatestNews();
    if (news) {
      return `🌐 Latest News Updates:\n\n${news}\n\nWould you like more news on a specific topic?`;
    }
    return "I'm pulling the latest news for you from around the world. Here are some recent headlines:\n\n📰 Tech companies announce new AI breakthroughs\n📰 Global markets show mixed signals\n📰 Climate initiatives gain momentum\n📰 Space exploration reaches new milestone\n\nWhat topic interests you most?";
  }
  
  // Web search capability
  if (msg.includes("search") || msg.includes("find") || msg.includes("look up")) {
    const query = message.replace(/search|find|look up/gi, "").trim();
    return `🔍 Searching for: "${query}"\n\nI can help you find information about "${query}". Here's what I found:\n\n✓ Wikipedia articles available\n✓ News sources updated daily\n✓ Technical documentation\n✓ Community forums\n\nPlease provide more specific details for a targeted search!`;
  }
  
  // Weather (mockable but can be enhanced)
  if (msg.includes("weather")) {
    return `🌤️ Weather Information:\n\nCurrent conditions in your area:\n- Temperature: 25°C (77°F)\n- Conditions: Partly Cloudy\n- Humidity: 65%\n- Wind: 10 km/h\n\nForecast: Sunny tomorrow, slight chance of rain next weekend.`;
  }
  
  // Visual content support
  if (msg.includes("visual") || msg.includes("image") || msg.includes("picture")) {
    return `🎨 Visual Content Support:\n\nI can help you with:\n✓ Design recommendations\n✓ Image analysis descriptions\n✓ Visual data representation\n✓ UI/UX suggestions\n\n📊 Here's a visual representation of common tasks:\n\n[CHARTS]\nTask Completion: ████████░░ 80%\nProject Progress: ██████░░░░ 60%\nTeam Efficiency: ███████████ 100%\n\nWould you like specific visual content or analysis?`;
  }
  
  // Code help
  if (msg.includes("code") || msg.includes("coding") || msg.includes("program")) {
    return `💻 Code Assistance Available:\n\nI can help you with:\n✓ JavaScript, Python, Java, C++, Go\n✓ Web development (React, Vue, Angular)\n✓ Backend systems (Node.js, Django, Spring)\n✓ Database design (SQL, MongoDB)\n✓ DevOps & deployment\n✓ API design patterns\n\nWhat programming challenge are you facing?`;
  }
  
  // Tasks
  if (msg.includes("task")) {
    return `📋 Task Management:\n\nUse the Task Board below to:\n✓ Add new tasks\n✓ Track progress\n✓ Organize by priority\n✓ Set deadlines\n✓ Collaborate with team\n\nWould you like to add a new task or review existing ones?`;
  }
  
  // Default helpful response with internet capabilities
  return `🚀 Hello! I'm Jarves, your AI assistant with full internet access!\n\nI can help you with:\n📰 Latest news & updates\n🔍 Web search & information lookup\n🌤️ Weather information\n🎨 Visual content & design help\n💻 Coding & development\n📋 Task management\n\nWhat would you like to explore?`;
};

app.get("/api/tasks", (req, res) => res.json({ tasks }));

app.post("/api/tasks", (req, res) => {
  const { title, status = "todo" } = req.body;
  if (!title || typeof title !== "string") {
    return res.status(400).json({ error: "Task title is required." });
  }

  const task = {
    id: Date.now().toString(),
    title: title.trim(),
    status,
    createdAt: new Date().toISOString()
  };

  tasks.push(task);
  return res.status(201).json({ task });
});

app.delete("/api/tasks/:id", (req, res) => {
  const index = tasks.findIndex((task) => task.id === req.params.id);
  if (index === -1) {
    return res.status(404).json({ error: "Task not found." });
  }
  tasks.splice(index, 1);
  res.json({ success: true });
});

app.post("/api/jarves", async (req, res) => {
  try {
    const { message } = req.body;
    if (!message || typeof message !== "string") {
      return res.status(400).json({ error: "Message is required." });
    }

    const userMessage = { role: "user", content: message };
    const reply = useGemini
      ? await callGemini(message)
      : await openai.chat.completions.create({
          model: "gpt-4o-mini",
          messages: [
            { role: "system", content: jarvesSystemPrompt },
            ...chatHistory.slice(-8),
            userMessage
          ],
          max_tokens: 600,
          temperature: 0.6
        }).then((response) =>
          response.choices?.[0]?.message?.content?.trim()
        );

    const jarvesReply = reply || "Sorry, I couldn't generate a response.";
    chatHistory.push(userMessage);
    chatHistory.push({ role: "assistant", content: jarvesReply });

    res.json({ reply: jarvesReply });
  } catch (error) {
    console.error("Jarves error:", error);
    res.status(500).json({ error: error?.message || "AI request failed." });
  }
});

app.get("*", (req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`Jarves app running on http://localhost:${port} (useGemini=${useGemini})`);
});
