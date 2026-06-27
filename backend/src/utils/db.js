const { exec } = require('child_process');
const { promisify } = require('util');

const execPromise = promisify(exec);

async function query(sql, params = []) {
  try {
    let formattedSql = sql;
    if (params.length > 0) {
      let i = 0;
      formattedSql = sql.replace(/\?/g, () => {
        const val = params[i++];
        if (val === null || val === undefined) return 'NULL';
        if (typeof val === 'number') return val;
        // Escape single quotes for SQL
        const escaped = String(val).replace(/'/g, "''");
        return `'${escaped}'`;
      });
    }

    // Escape for shell: we'll wrap the whole command in single quotes, 
    // so we need to handle single quotes in the SQL.
    // The team-db CLI expects the SQL as a single argument.
    // If we use `team-db "..."`, we need to escape double quotes and backslashes.
    
    const command = `team-db "${formattedSql.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
    
    const { stdout, stderr } = await execPromise(command);
    if (stderr) {
      console.error('DB Stderr:', stderr);
    }
    return JSON.parse(stdout);
  } catch (error) {
    console.error('DB Error:', error);
    console.error('SQL:', sql);
    throw error;
  }
}

module.exports = { query };
