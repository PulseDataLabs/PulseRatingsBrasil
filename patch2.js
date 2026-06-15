    // ── Main View Switching ───────────────────────────────────
    $('.main-tab-btn').on('click', function() {
      $('.main-tab-btn').removeClass('active');
      $(this).addClass('active');
      
      const target = $(this).data('target');
      $('.main-view').removeClass('active');
      $('#' + target).addClass('active');

      if (target === 'view-comparador') {
        renderComparator();
      }
    });

    // ── Comparator Logic ──────────────────────────────────────────
    const $compSectorFilter = $('#comp-sector-filter');
    const $compCardsContainer = $('#comp-cards-container');
    const $comparatorContent = $('#comparator-content');

    $compSectorFilter.on('change', renderComparator);

    function getRatingScore(rating) {
      const r = rating.toUpperCase();
      if (r.includes('AAA') || r.includes('AAA')) return 100;
      if (r.includes('AA+') || r.includes('AA1')) return 95;
      if (r.includes('AA') || r.includes('AA2')) return 90;
      if (r.includes('AA-') || r.includes('AA3')) return 85;
      if (r.includes('A+') || r.includes('A1')) return 80;
      if (r.includes('A') || r.includes('A2')) return 75;
      if (r.includes('A-') || r.includes('A3')) return 70;
      if (r.includes('BBB+') || r.includes('BAA1')) return 65;
      if (r.includes('BBB') || r.includes('BAA2')) return 60;
      if (r.includes('BBB-') || r.includes('BAA3')) return 55;
      if (r.includes('BB+') || r.includes('BA1')) return 50;
      if (r.includes('BB') || r.includes('BA2')) return 45;
      if (r.includes('BB-') || r.includes('BA3')) return 40;
      if (r.includes('B+') || r.includes('B1')) return 35;
      if (r.includes('B') || r.includes('B2')) return 30;
      if (r.includes('B-') || r.includes('B3')) return 25;
      if (r.includes('CCC') || r.includes('CAA')) return 20;
      if (r.includes('CC') || r.includes('CA')) return 15;
      if (r.includes('C')) return 10;
      if (r.includes('D') || r.includes('SD')) return 0;
      return 10; // fallback
    }

    function renderComparator() {
      const sector = $compSectorFilter.val();
      if (!sector) {
        $compCardsContainer.hide();
        $comparatorContent.html(`
          <div class="empty-state" style="text-align: center; padding: 4rem 1rem; background: var(--surface); border: 1px dashed var(--border1); border-radius: var(--radius-lg); color: var(--text3);">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="opacity: 0.5; margin-bottom: 1rem;"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
            <p>Selecione um setor acima para visualizar a matriz comparativa.</p>
          </div>
        `);
        return;
      }

      const emissoresNoSetor = [];
      const agencyCount = {};
      let topEmissor = null;
      let topRatingVal = -1;

      for (const [emissor, data] of Object.entries(byEmissor)) {
        const firstRow = data.rows[0];
        if (firstRow && firstRow.setor === sector) {
          emissoresNoSetor.push({ emissor, rows: data.rows });
          
          let maxScore = 0;
          for (const row of data.rows) {
            agencyCount[row.agencia] = (agencyCount[row.agencia] || 0) + 1;
            const score = getRatingScore(row.rating);
            if (score > maxScore) maxScore = score;
          }
          if (maxScore > topRatingVal) {
            topRatingVal = maxScore;
            topEmissor = emissor;
          }
        }
      }

      $('#comp-total-emissores').text(emissoresNoSetor.length);
      $('#comp-top-emissor').text(topEmissor || '—');
      
      let topAgencia = Object.keys(agencyCount).sort((a,b) => agencyCount[b] - agencyCount[a])[0];
      $('#comp-top-agencia').html(topAgencia ? agencyBadge(topAgencia) : '—');
      $compCardsContainer.show();

      if (emissoresNoSetor.length === 0) {
        $comparatorContent.html('<p>Nenhum emissor encontrado para este setor.</p>');
        return;
      }

      const allSectorAgencies = Object.keys(agencyCount).sort();
      emissoresNoSetor.sort((a, b) => a.emissor.localeCompare(b.emissor));

      let matrixHtml = `
        <div class="comp-matrix-wrapper">
          <table class="comp-matrix">
            <thead>
              <tr>
                <th>Emissor</th>
                ${allSectorAgencies.map(a => `<th>${a}</th>`).join('')}
              </tr>
            </thead>
            <tbody>
      `;

      for (const item of emissoresNoSetor) {
        matrixHtml += `<tr><td>${item.emissor}</td>`;
        
        for (const ag of allSectorAgencies) {
          const agRows = item.rows.filter(r => r.agencia === ag);
          if (agRows.length === 0) {
            matrixHtml += `<td><span style="color:var(--text3)">—</span></td>`;
          } else {
            const uniqueRatings = [...new Set(agRows.map(r => r.rating).filter(Boolean))];
            matrixHtml += `<td><div class="comp-rating-stack">`;
            for (const rating of uniqueRatings) {
              matrixHtml += `<span class="rating-cell" style="display:inline-block">${rating}</span>`;
            }
            matrixHtml += `</div></td>`;
          }
        }
        matrixHtml += `</tr>`;
      }

      matrixHtml += `
            </tbody>
          </table>
        </div>
      `;

      $comparatorContent.html(matrixHtml);
    }
