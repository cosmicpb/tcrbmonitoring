/**
 * Cloudflare Worker para monitoramento T CrB
 * Este worker é executado periodicamente via Cron Triggers
 */

// Função para fazer scraping (adaptada para Cloudflare Workers)
async function scrapeLatestObservation() {
  const AAVSO_URL = 'https://apps.aavso.org/webobs/results/?star=t+crb&num_results=20&obs_types=all&page=1';
  
  try {
    const response = await fetch(AAVSO_URL);
    const html = await response.text();
    
    // Parse HTML usando regex (Cloudflare Workers não tem cheerio)
    // Procura pela primeira linha da tabela
    const tableMatch = html.match(/<tbody>([\s\S]*?)<\/tbody>/);
    if (!tableMatch) {
      throw new Error('Tabela não encontrada');
    }
    
    const tbody = tableMatch[1];
    const firstRowMatch = tbody.match(/<tr class="obs[^"]*"[^>]*>([\s\S]*?)<\/tr>/);
    
    if (!firstRowMatch) {
      throw new Error('Nenhuma observação encontrada');
    }
    
    const row = firstRowMatch[1];
    const cells = row.match(/<td[^>]*>([\s\S]*?)<\/td>/g) || [];
    
    // Extrai o texto de cada célula
    const getText = (cell) => {
      const match = cell.match(/>([^<]+)</);
      return match ? match[1].trim() : '';
    };
    
    const data = {
      star: getText(cells[1] || ''),
      jd: getText(cells[2] || ''),
      calendarDate: getText(cells[3] || ''),
      magnitude: getText(cells[4] || ''),
      error: getText(cells[5] || ''),
      filter: getText(cells[6] || ''),
      observer: getText(cells[7] || ''),
      timestamp: new Date().toISOString()
    };
    
    return data;
  } catch (error) {
    throw new Error(`Erro ao fazer scraping: ${error.message}`);
  }
}

// Handler para Cron Trigger
async function handleScheduled(event, env) {
  try {
    console.log('Iniciando monitoramento T CrB...');
    
    const data = await scrapeLatestObservation();
    console.log('Dados extraídos:', data);
    
    // Se você configurou D1 Database, salve aqui
    if (env.DB) {
      // Verifica se já existe
      const existing = await env.DB.prepare(
        'SELECT COUNT(*) as count FROM observations WHERE jd = ?'
      ).bind(data.jd).first();
      
      if (existing && existing.count > 0) {
        console.log('Observação já existe no banco');
        return { status: 'duplicate', data };
      }
      
      // Insere nova observação
      await env.DB.prepare(`
        INSERT INTO observations (star, jd, calendar_date, magnitude, error, filter, observer, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `).bind(
        data.star,
        data.jd,
        data.calendarDate,
        data.magnitude,
        data.error,
        data.filter,
        data.observer,
        data.timestamp
      ).run();
      
      console.log('Nova observação salva no banco');
      return { status: 'saved', data };
    }
    
    // Se não tem DB configurado, apenas retorna os dados
    return { status: 'success', data };
    
  } catch (error) {
    console.error('Erro no monitoramento:', error.message);
    return { status: 'error', error: error.message };
  }
}

// Handler para requisições HTTP (opcional, para testes)
async function handleRequest(request) {
  try {
    const data = await scrapeLatestObservation();
    
    return new Response(JSON.stringify({
      success: true,
      data,
      timestamp: new Date().toISOString()
    }), {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      error: error.message
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }
}

// Export do worker
export default {
  // Handler para Cron Triggers
  async scheduled(event, env, ctx) {
    ctx.waitUntil(handleScheduled(event, env));
  },
  
  // Handler para requisições HTTP
  async fetch(request, env, ctx) {
    return handleRequest(request);
  }
};