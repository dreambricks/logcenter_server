const decryptText = async () => {
    try {
        const fileInput = document.getElementById("decript_key");
        const file = fileInput.files[0];

        if (!file) {
            alert('Por favor, selecione o arquivo da chave privada.');
            return;
        }

        const reader = new FileReader();
        reader.onload = async (e) => {
            console.log('Private key loaded');
            const privateKey = e.target.result;

            try {
                // Fetch encrypted data from endpoint
                const project = getQueryParam('project');
                if (!project) {
                    alert("Parâmetro 'project' não encontrado na URL.");
                    return;
                }

                const response = await fetch(`/datalog/getdatabyproject?project=${project}`);
                const data = await response.json();

                const encryptedLines = Array.isArray(data.data)
                ? data.data.map(item => item.additional).filter(Boolean)
                : data.data?.additional ? [data.data.additional] : [];

                console.log('Encrypted data loaded');

                // Decrypt each line
                const decryptedLines = [];
                for (const line of encryptedLines) {
                    if (line.trim()) {
                        try {
                            const decryptedLine = await dbDecryptString(line.trim(), privateKey);
                            decryptedLines.push(decryptedLine);
                        } catch (err) {
                            console.warn('Falha ao descriptografar uma linha. Pulando...', err);
                            // Linha com erro será ignorada
                        }
                    }
                }

                console.log('Decrypted data');
                // console.log(decryptedLines);

                // Create CSV content
                const csvContent = [
                    ...decryptedLines
                ].join('\n');

                // Create and trigger download
                const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.setAttribute('href', url);
                link.setAttribute('download', 'dados_maquina.csv');
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

            } catch(err) {
                console.log('Falha na descriptografia: Chave privada inválida ou dados corrompidos');
                console.error(err);
            }
        };

        reader.readAsText(file);
    } catch(err) {
        console.log('Erro ao ler arquivo da chave privada');
        console.error(err);
    }
};

function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}
