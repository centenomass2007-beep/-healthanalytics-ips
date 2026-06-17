const express = require('express');
const path = require('path');
const { Pool } = require('pg');

const app = express();
const PORT = process.env.PORT || 3000;

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const DIAGNOSTICOS = ['Hipertensión','Diabetes tipo 2','Obesidad','Cardiopatía isquémica','Asma','Hipotiroidismo','Artritis','Insuficiencia renal','Sin diagnóstico','Dislipidemia'];
const NOMBRES_M = ['Carlos','Luis','Juan','Pedro','Andrés','Miguel','Jorge','Roberto','Alejandro','Fernando','David','Diego','Sebastián','Ricardo','Mauricio'];
const NOMBRES_F = ['María','Ana','Claudia','Laura','Patricia','Sandra','Marcela','Gloria','Lucía','Valentina','Isabella','Camila','Natalia','Diana','Andrea'];
const APELLIDOS = ['García','López','Martínez','Rodríguez','Hernández','González','Pérez','Torres','Ramírez','Flores','Castro','Vargas','Moreno','Jiménez','Soto'];

function rand(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }
function randF(min, max, dec = 1) { return parseFloat((Math.random() * (max - min) + min).toFixed(dec)); }
function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

function calcRiesgo(p) {
  let score = 0;
  if (p.edad > 60) score += 2; else if (p.edad > 45) score += 1;
  if (p.glucosa > 200) score += 3; else if (p.glucosa > 126) score += 2; else if (p.glucosa > 100) score += 1;
  if (p.presion_sistolica > 180) score += 3; else if (p.presion_sistolica > 160) score += 2; else if (p.presion_sistolica > 140) score += 1;
  if (p.imc > 35) score += 2; else if (p.imc > 30) score += 1;
  if (p.colesterol > 240) score += 2; else if (p.colesterol > 200) score += 1;
  if (p.fumador) score += 2;
  if (p.antecedentes) score += 1;
  if (score >= 8) return 'Crítico';
  if (score >= 5) return 'Alto';
  if (score >= 3) return 'Medio';
  return 'Bajo';
}

function generarPaciente() {
  const sexo = Math.random() < 0.52 ? 'M' : 'F';
  const nombre = sexo === 'M' ? pick(NOMBRES_M) : pick(NOMBRES_F);
  const apellido = pick(APELLIDOS) + ' ' + pick(APELLIDOS);
  const edad = rand(18, 85);
  const peso = randF(45, 130, 1);
  const altura = randF(1.50, 1.95, 2);
  const imc = parseFloat((peso / (altura * altura)).toFixed(1));
  const glucosa = randF(60, 350, 1);
  const colesterol = randF(100, 320, 1);
  const presion_sistolica = rand(90, 220);
  const presion_diastolica = rand(60, 130);
  const frecuencia_cardiaca = rand(50, 130);
  const saturacion_oxigeno = randF(82, 100, 1);
  const temperatura = randF(36, 39.5, 1);
  const fumador = Math.random() < 0.22;
  const antecedentes = Math.random() < 0.4;
  const diagnostico = glucosa > 200 ? 'Diabetes tipo 2' : presion_sistolica > 160 ? 'Hipertensión' : imc > 35 ? 'Obesidad' : pick(DIAGNOSTICOS);
  const data = { edad, glucosa, presion_sistolica, imc, colesterol, fumador, antecedentes };
  const riesgo = calcRiesgo(data);
  return { nombre, apellido, sexo, edad, peso, altura, imc, glucosa, colesterol, presion_sistolica, presion_diastolica, frecuencia_cardiaca, saturacion_oxigeno, temperatura, fumador, antecedentes, diagnostico, riesgo };
}

async function initDB() {
  const fs = require('fs');
  const schema = fs.readFileSync(path.join(__dirname, 'db', 'schema.sql'), 'utf8');
  try {
    await pool.query(schema);
    console.log('Base de datos inicializada');
    const count = await pool.query('SELECT COUNT(*) FROM pacientes');
    if (parseInt(count.rows[0].count) === 0) {
      console.log('Poblando base de datos con 1800 pacientes...');
      for (let i = 0; i < 1800; i++) {
        const p = generarPaciente();
        await pool.query(
          `INSERT INTO pacientes (nombre, apellido, sexo, edad, peso, altura, imc, glucosa, colesterol,
            presion_sistolica, presion_diastolica, frecuencia_cardiaca, saturacion_oxigeno, temperatura,
            fumador, antecedentes, diagnostico, riesgo, fecha_registro)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,
            DATE '2024-01-01' + (random() * 364)::int)`,
          [p.nombre, p.apellido, p.sexo, p.edad, p.peso, p.altura, p.imc, p.glucosa, p.colesterol,
           p.presion_sistolica, p.presion_diastolica, p.frecuencia_cardiaca, p.saturacion_oxigeno,
           p.temperatura, p.fumador, p.antecedentes, p.diagnostico, p.riesgo]
        );
      }
      console.log('Insertando usuarios demo...');
      await pool.query(
        `INSERT INTO usuarios (nombre, email, rol, password_hash) VALUES
         ('Admin Sistema', 'admin@healthanalytics.co', 'admin', 'admin123'),
         ('Dr. Juan Pérez', 'j.perez@healthanalytics.co', 'medico', 'medico123'),
         ('Ana Martínez', 'a.martinez@healthanalytics.co', 'analista', 'analista123')
         ON CONFLICT (email) DO NOTHING`
      );
      console.log('Insertando historial ETL...');
      await pool.query(
        `INSERT INTO historial_etl (fecha, usuario, registros_originales, registros_limpios, duplicados_eliminados, nulos_imputados, tiempo_ejecucion, estado) VALUES
         ('2024-11-15 08:30', 'admin', 1800, 1800, 50, 143, '4.2s', 'ok'),
         ('2024-11-14 14:15', 'analista', 1800, 1800, 50, 143, '3.8s', 'ok'),
         ('2024-11-13 09:00', 'admin', 1200, 0, 0, 0, '1.1s', 'err')
         ON CONFLICT DO NOTHING`
      );
      console.log('Insertando métricas ML...');
      await pool.query(
        `INSERT INTO metricas_ml (algoritmo, accuracy, precision, recall, f1_score) VALUES
         ('Random Forest', 87.4, 86.1, 88.2, 87.1),
         ('Árbol de Decisión', 82.1, 81.3, 83.4, 82.3),
         ('Regresión Logística', 79.3, 78.9, 80.1, 79.5)
         ON CONFLICT DO NOTHING`
      );
      console.log('Base de datos poblada correctamente.');
    } else {
      console.log(`BD ya tiene datos: ${count.rows[0].count} pacientes`);
    }
  } catch (e) {
    console.error('Error inicializando BD:', e.message);
  }
}

// ============= API PACIENTES =============

app.get('/api/pacientes', async (req, res) => {
  try {
    const { search, riesgo, sexo, page = 1, limit = 20 } = req.query;
    let sql = 'SELECT * FROM pacientes WHERE 1=1';
    const params = [];
    let idx = 1;

    if (search) {
      sql += ` AND (LOWER(nombre || ' ' || apellido) LIKE LOWER($${idx}) OR CAST(id AS TEXT) LIKE $${idx} OR LOWER(diagnostico) LIKE LOWER($${idx}))`;
      params.push(`%${search}%`);
      idx++;
    }
    if (riesgo) {
      sql += ` AND riesgo = $${idx}`;
      params.push(riesgo);
      idx++;
    }
    if (sexo) {
      sql += ` AND sexo = $${idx}`;
      params.push(sexo);
      idx++;
    }

    const countResult = await pool.query(sql.replace('SELECT *', 'SELECT COUNT(*)'), params);
    const total = parseInt(countResult.rows[0].count);

    const offset = (parseInt(page) - 1) * parseInt(limit);
    sql += ` ORDER BY id ASC LIMIT $${idx} OFFSET $${idx + 1}`;
    params.push(parseInt(limit), offset);

    const result = await pool.query(sql, params);
    res.json({ pacientes: result.rows, total, page: parseInt(page), pages: Math.ceil(total / parseInt(limit)) });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/api/pacientes/criticos', async (req, res) => {
  try {
    const result = await pool.query(
      "SELECT * FROM pacientes WHERE riesgo IN ('Crítico', 'Alto') ORDER BY presion_sistolica DESC LIMIT 8"
    );
    res.json(result.rows);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/api/pacientes/resumen', async (req, res) => {
  try {
    const total = await pool.query('SELECT COUNT(*) FROM pacientes');
    const criticos = await pool.query("SELECT COUNT(*) FROM pacientes WHERE riesgo = 'Crítico'");
    const alto = await pool.query("SELECT COUNT(*) FROM pacientes WHERE riesgo = 'Alto'");
    const hipertensos = await pool.query("SELECT COUNT(*) FROM pacientes WHERE diagnostico LIKE '%Hipertensión%'");
    const diabeticos = await pool.query("SELECT COUNT(*) FROM pacientes WHERE diagnostico LIKE '%Diabetes%'");
    const fumadores = await pool.query('SELECT COUNT(*) FROM pacientes WHERE fumador = true');

    const riesgoCounts = await pool.query(
      "SELECT riesgo, COUNT(*) FROM pacientes GROUP BY riesgo ORDER BY riesgo"
    );

    res.json({
      total: parseInt(total.rows[0].count),
      criticos: parseInt(criticos.rows[0].count),
      alto: parseInt(alto.rows[0].count),
      hipertensos: parseInt(hipertensos.rows[0].count),
      diabeticos: parseInt(diabeticos.rows[0].count),
      fumadores: parseInt(fumadores.rows[0].count),
      riesgo_counts: riesgoCounts.rows
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/api/pacientes', async (req, res) => {
  try {
    const p = req.body;
    const imc = parseFloat((p.peso / (p.altura * p.altura)).toFixed(1));
    let score = 0;
    if (p.edad > 60) score += 2; else if (p.edad > 45) score += 1;
    if (p.glucosa > 200) score += 3; else if (p.glucosa > 126) score += 2; else if (p.glucosa > 100) score += 1;
    if (p.presion_sistolica > 180) score += 3; else if (p.presion_sistolica > 160) score += 2; else if (p.presion_sistolica > 140) score += 1;
    if (imc > 35) score += 2; else if (imc > 30) score += 1;
    if (p.colesterol > 240) score += 2; else if (p.colesterol > 200) score += 1;
    if (p.fumador) score += 2;
    if (p.antecedentes) score += 1;
    const riesgo = score >= 8 ? 'Crítico' : score >= 5 ? 'Alto' : score >= 3 ? 'Medio' : 'Bajo';

    const result = await pool.query(
      `INSERT INTO pacientes (nombre, apellido, sexo, edad, peso, altura, imc, glucosa, colesterol,
        presion_sistolica, presion_diastolica, frecuencia_cardiaca, saturacion_oxigeno, temperatura,
        fumador, antecedentes, diagnostico, riesgo)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18) RETURNING *`,
      [p.nombre, p.apellido, p.sexo, p.edad, p.peso, p.altura, imc, p.glucosa, p.colesterol,
       p.presion_sistolica, p.presion_diastolica || 80, p.frecuencia_cardiaca || 75,
       p.saturacion_oxigeno || 98, p.temperatura || 36.6, p.fumador || false,
       p.antecedentes || false, p.diagnostico, riesgo]
    );
    res.json(result.rows[0]);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ============= API ESTADÍSTICAS =============

app.get('/api/estadisticas', async (req, res) => {
  try {
    const stats = await pool.query(`
      SELECT
        ROUND(AVG(glucosa)::numeric, 1) as media_glucosa,
        ROUND(AVG(colesterol)::numeric, 1) as media_colesterol,
        ROUND(AVG(imc)::numeric, 1) as media_imc,
        ROUND(AVG(edad)::numeric, 1) as media_edad,
        ROUND(AVG(frecuencia_cardiaca)::numeric, 1) as media_fc,
        ROUND(AVG(presion_sistolica)::numeric, 0) as media_presion_sistolica,
        ROUND(STDDEV(imc)::numeric, 1) as desv_imc,
        (SELECT diagnostico FROM pacientes GROUP BY diagnostico ORDER BY COUNT(*) DESC LIMIT 1) as moda_diagnostico,
        (SELECT COUNT(*) FROM pacientes WHERE sexo = 'M') as hombres,
        (SELECT COUNT(*) FROM pacientes WHERE sexo = 'F') as mujeres
      FROM pacientes
    `);
    res.json(stats.rows[0]);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/api/diagnosticos/top', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT diagnostico, COUNT(*) as count FROM pacientes GROUP BY diagnostico ORDER BY count DESC LIMIT 5'
    );
    res.json(result.rows);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ============= API ETL =============

app.post('/api/etl/ejecutar', async (req, res) => {
  try {
    const inicio = Date.now();

    const duplicados = await pool.query(
      `SELECT COUNT(*) as count FROM (SELECT id_paciente, COUNT(*) FROM pacientes GROUP BY id_paciente HAVING COUNT(*) > 1) sub`
    );

    const nulos = await pool.query(
      `SELECT COUNT(*) as count FROM pacientes WHERE
        nombre IS NULL OR glucosa IS NULL OR colesterol IS NULL OR presion_sistolica IS NULL`
    );

    const count = await pool.query('SELECT COUNT(*) FROM pacientes');
    const totalLimpios = parseInt(count.rows[0].count);
    const dupCount = parseInt(duplicados.rows[0].count);
    const nullCount = parseInt(nulos.rows[0].count);
    const elapsed = ((Date.now() - inicio) / 1000).toFixed(1);

    await pool.query(
      `INSERT INTO historial_etl (usuario, registros_originales, registros_limpios, duplicados_eliminados, nulos_imputados, tiempo_ejecucion, estado)
       VALUES ($1, $2, $3, $4, $5, $6, 'ok')`,
      [req.body.usuario || 'admin', totalLimpios, totalLimpios, dupCount, nullCount, elapsed + 's']
    );

    res.json({ registros_originales: totalLimpios, duplicados: dupCount, nulos: nullCount, registros_finales: totalLimpios, tiempo: elapsed + 's' });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/api/etl/historial', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM historial_etl ORDER BY fecha DESC LIMIT 6');
    res.json(result.rows);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ============= API USUARIOS =============

app.get('/api/usuarios', async (req, res) => {
  try {
    const result = await pool.query('SELECT id, nombre, email, rol, activo, ultimo_acceso FROM usuarios ORDER BY id');
    res.json(result.rows);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/api/usuarios', async (req, res) => {
  try {
    const result = await pool.query(
      'INSERT INTO usuarios (nombre, email, rol, password_hash) VALUES ($1, $2, $3, $4) RETURNING id, nombre, email, rol, activo',
      [req.body.nombre, req.body.email, req.body.rol, req.body.password || 'default123']
    );
    res.json(result.rows[0]);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/api/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    const result = await pool.query('SELECT * FROM usuarios WHERE email = $1 AND password_hash = $2', [email, password]);
    if (result.rows.length === 0) return res.status(401).json({ error: 'Credenciales incorrectas' });
    const u = result.rows[0];
    await pool.query('UPDATE usuarios SET ultimo_acceso = NOW() WHERE id = $1', [u.id]);
    res.json({ id: u.id, name: u.nombre, email: u.email, role: u.rol });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.put('/api/usuarios/:id/toggle', async (req, res) => {
  try {
    const result = await pool.query(
      'UPDATE usuarios SET activo = NOT activo WHERE id = $1 RETURNING id, nombre, activo',
      [req.params.id]
    );
    res.json(result.rows[0]);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ============= API ML =============

app.get('/api/ml/metricas', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM metricas_ml ORDER BY accuracy DESC');
    res.json(result.rows);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ============= FALLBACK SPA =============

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ============= INICIO =============

initDB().then(() => {
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`HealthAnalytics IPS corriendo en puerto ${PORT}`);
    console.log(`Entorno: ${process.env.NODE_ENV || 'development'}`);
  });
});
