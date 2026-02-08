const express = require("express");
const cors = require("cors");
const { Pool } = require("pg");

const app = express();
const PORT = 3001; // Different port to avoid conflicts

// ✅ Local Development CORS (Allow all origins for testing)
app.use(cors({
  origin: true, // Allow all origins for local development
  credentials: true,
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
}));

app.use(express.json());

// ✅ Database Configuration (same as Render: use env; default localhost so no IP needed)
const dbConfig = {
  user: process.env.DB_USER || "postgres",
  password: process.env.DB_PASSWORD || "",
  host: process.env.DB_HOST || "localhost",
  port: parseInt(process.env.DB_PORT || "5432", 10),
  database: process.env.DB_NAME || "labdb2",
  ssl: process.env.DB_SSL === "true" ? { rejectUnauthorized: false } : false,
  connectionTimeoutMillis: 10000,
  idleTimeoutMillis: 30000,
  max: 10,
};

console.log("🔧 Connecting to PostgreSQL at:", dbConfig.host + ":" + dbConfig.port + "/" + dbConfig.database);

// ✅ Create PostgreSQL Connection Pool
let pool;
async function initDatabase() {
  try {
    pool = new Pool(dbConfig);
    
    // Test connection
    const result = await pool.query('SELECT NOW() as current_time, version() as pg_version');
    console.log("✅ Connected to PostgreSQL successfully!");
    console.log("📅 Server time:", result.rows[0].current_time);
    console.log("🗄️ PostgreSQL version:", result.rows[0].pg_version.split(' ')[0] + ' ' + result.rows[0].pg_version.split(' ')[1]);
    
    // Test if our trading tables exist
    const tablesResult = await pool.query(`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public' 
      ORDER BY table_name;
    `);
    
    console.log("📋 Available tables:", tablesResult.rows.map(r => r.table_name).join(', '));
    
  } catch (error) {
    console.error("❌ Database connection failed:", error.message);
    console.error("🔧 Make sure PostgreSQL is running at", dbConfig.host + ":" + dbConfig.port);
    process.exit(1);
  }
}

// ✅ Health Check Route
app.get("/", async (req, res) => {
  try {
    const result = await pool.query('SELECT NOW() as server_time');
    res.json({
      status: "✅ Local server is working!",
      database: "✅ PostgreSQL connected",
      server_time: result.rows[0].server_time,
      host: dbConfig.host,
      database_name: dbConfig.database
    });
  } catch (error) {
    res.status(500).json({
      status: "❌ Server error",
      error: error.message
    });
  }
});

// ✅ API: Fetch All Trades
app.get("/api/trades", async (req, res) => {
  try {
    console.log("🔍 [Trades] Request received");
    
    const result = await pool.query("SELECT * FROM alltraderecords ORDER BY timestamp DESC LIMIT 100;");
    
    console.log("✅ [Trades] Fetched", result.rows.length, "trades");
    if (result.rows.length > 0) {
      console.log("📊 [Trades] Latest trade:", {
        timestamp: result.rows[0].timestamp,
        pair: result.rows[0].pair || result.rows[0].symbol,
        action: result.rows[0].action || result.rows[0].side
      });
    }
    
    res.json({ 
      trades: result.rows,
      count: result.rows.length,
      source: "Ubuntu Server Database"
    });
  } catch (error) {
    console.error("❌ [Trades] Error:", error.message);
    res.status(500).json({ 
      error: error.message,
      hint: "Check if 'alltraderecords' table exists in the database"
    });
  }
});

// ✅ API: Fetch Machines
app.get("/api/machines", async (req, res) => {
  try {
    console.log("🔍 [Machines] Request received");
    
    const result = await pool.query("SELECT machineid, active FROM machines ORDER BY machineid;");
    
    console.log("✅ [Machines] Fetched", result.rows.length, "machines");
    
    res.json({ 
      machines: result.rows,
      count: result.rows.length,
      source: "Ubuntu Server Database"
    });
  } catch (error) {
    console.error("❌ [Machines] Error:", error.message);
    res.status(500).json({ 
      error: error.message,
      hint: "Check if 'machines' table exists in the database"
    });
  }
});

// ✅ API: Test Database Tables
app.get("/api/tables", async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT table_name, 
             (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
      FROM information_schema.tables t
      WHERE table_schema = 'public' 
      ORDER BY table_name;
    `);
    
    res.json({
      tables: result.rows,
      count: result.rows.length,
      database: dbConfig.database
    });
  } catch (error) {
    console.error("❌ [Tables] Error:", error.message);
    res.status(500).json({ error: error.message });
  }
});

// ✅ API: Fetch SignalProcessingLogs  
app.get("/api/signalprocessinglogs", async (req, res) => {
  try {
    console.log("🔍 [SignalLogs] Request received");
    
    const result = await pool.query("SELECT * FROM signalprocessinglogs ORDER BY timestamp DESC LIMIT 100;");
    
    console.log("✅ [SignalLogs] Fetched", result.rows.length, "signal logs");
    
    res.json({ 
      logs: result.rows,
      count: result.rows.length,
      source: "Ubuntu Server Database"
    });
  } catch (error) {
    console.error("❌ [SignalLogs] Error:", error.message);
    res.status(500).json({ 
      error: error.message,
      hint: "Check if 'signalprocessinglogs' table exists in the database"
    });
  }
});

// ✅ Initialize and Start Server
async function startServer() {
  await initDatabase();
  
  app.listen(PORT, () => {
    console.log("\n🚀 Local Server Started Successfully!");
    console.log("📍 Server URL: http://localhost:" + PORT);
    console.log("🗄️ Database: " + dbConfig.host + ":" + dbConfig.port + "/" + dbConfig.database);
    console.log("\n📋 Available endpoints:");
    console.log("   GET  /                     - Health check");
    console.log("   GET  /api/trades           - Fetch trading records");
    console.log("   GET  /api/machines         - Fetch machine status");
    console.log("   GET  /api/tables           - List all database tables");
    console.log("   GET  /api/signalprocessinglogs - Fetch signal logs");
    console.log("\n✨ Ready to serve data from your Ubuntu trading server!");
  });
}

// ✅ Handle graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n🔄 Shutting down server...');
  if (pool) {
    await pool.end();
    console.log('✅ Database connections closed');
  }
  process.exit(0);
});

// ✅ Start the server
startServer().catch(error => {
  console.error("❌ Failed to start server:", error);
  process.exit(1);
});
