import pg from 'pg';
import dotenv from 'dotenv';
dotenv.config();

const connectionString = process.env.DATABASE_URL;
console.log('Testing connection to:', connectionString);

const client = new pg.Client({
  connectionString: connectionString,
});

async function test() {
  try {
    await client.connect();
    console.log('Connected successfully!');
    const res = await client.query('SELECT current_database()');
    console.log('Database:', res.rows[0]);
    await client.end();
  } catch (err) {
    console.error('Connection error:', err);
    process.exit(1);
  }
}

test();
