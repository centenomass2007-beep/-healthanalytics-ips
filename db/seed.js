const { Client } = require('pg');

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

function generarPaciente(id) {
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

async function seed() {
  const client = new Client({ connectionString: process.env.DATABASE_URL || 'postgresql://localhost:5432/healthanalytics_db' });
  await client.connect();

  console.log('Insertando 1800 pacientes...');
  for (let i = 0; i < 1800; i++) {
    const p = generarPaciente(i + 1);
    await client.query(
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

  console.log('Insertando usuarios...');
  await client.query(
    `INSERT INTO usuarios (nombre, email, rol, password_hash) VALUES
     ('Admin Sistema', 'admin@healthanalytics.co', 'admin', 'admin123'),
     ('Dr. Juan Pérez', 'j.perez@healthanalytics.co', 'medico', 'medico123'),
     ('Ana Martínez', 'a.martinez@healthanalytics.co', 'analista', 'analista123')
     ON CONFLICT (email) DO NOTHING`
  );

  console.log('Insertando historial ETL...');
  await client.query(
    `INSERT INTO historial_etl (fecha, usuario, registros_originales, registros_limpios, duplicados_eliminados, nulos_imputados, tiempo_ejecucion, estado) VALUES
     ('2024-11-15 08:30', 'admin', 1800, 1800, 50, 143, '4.2s', 'ok'),
     ('2024-11-14 14:15', 'analista', 1800, 1800, 50, 143, '3.8s', 'ok'),
     ('2024-11-13 09:00', 'admin', 1200, 0, 0, 0, '1.1s', 'err')
     ON CONFLICT DO NOTHING`
  );

  console.log('Insertando métricas ML...');
  await client.query(
    `INSERT INTO metricas_ml (algoritmo, accuracy, precision, recall, f1_score) VALUES
     ('Random Forest', 87.4, 86.1, 88.2, 87.1),
     ('Árbol de Decisión', 82.1, 81.3, 83.4, 82.3),
     ('Regresión Logística', 79.3, 78.9, 80.1, 79.5)
     ON CONFLICT DO NOTHING`
  );

  await client.end();
  console.log('Base de datos inicializada correctamente.');
}

seed().catch(e => { console.error('Error seeding database:', e.message); process.exit(1); });
