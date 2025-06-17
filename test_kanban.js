const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));

async function testKanbanData() {
    try {
        console.log('🧪 Testando dados do KanbanBoard...\n');

        // Login
        const loginRes = await fetch('http://localhost:8000/api/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email: 'test@example.com', password: 'Test123!@#'})
        });
        
        const loginData = await loginRes.json();
        const token = loginData.data.tokens.accessToken;
        
        const statuses = ['NOVA', 'LIDA', 'ENVIADA_PARA_ADV', 'CONCLUIDA'];
        
        for (const status of statuses) {
            console.log(`📊 Testando status: ${status}`);
            
            const pubRes = await fetch(`http://localhost:8000/api/publications?page=1&limit=30&status=${status}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!pubRes.ok) {
                console.log(`❌ Erro para status ${status}:`, pubRes.status);
                const errorData = await pubRes.json();
                console.log('Erro:', errorData);
                continue;
            }
            
            const pubData = await pubRes.json();
            console.log(`✅ Status ${status}: ${pubData.data.data.length} publicações encontradas`);
            console.log(`   Total: ${pubData.data.total}, Página: ${pubData.data.page}/${pubData.data.totalPages}\n`);
        }
        
        // Teste sem filtro de status
        console.log('📊 Testando sem filtro de status:');
        const allRes = await fetch('http://localhost:8000/api/publications?page=1&limit=30', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (allRes.ok) {
            const allData = await allRes.json();
            console.log(`✅ Sem filtro: ${allData.data.data.length} publicações encontradas`);
            console.log(`   Total: ${allData.data.total}\n`);
        } else {
            console.log('❌ Erro ao buscar sem filtro:', allRes.status);
        }
        
    } catch (error) {
        console.error('❌ Erro durante o teste:', error.message);
    }
}

testKanbanData(); 