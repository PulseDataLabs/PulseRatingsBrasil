    function safeDestroyTable() {
      if (!tableApi) return;
      const $wrapper = $('#ratings-table_wrapper');
      if ($wrapper.length) {
        const $length   = $('.dt-length-placeholder');
        const $info     = $('.dt-info-placeholder');
        const $paginate = $('.dt-paginate-placeholder');
        $wrapper.append($length, $info, $paginate);
      }
      tableApi.destroy();
      tableApi = null;
    }

    $toggleConsolidated.on('change', function () {
      isConsolidated = this.checked;
      closeDrawer();

      safeDestroyTable();
      $table.find('tbody').empty();
      buildColumnDefs(isConsolidated);

      tableApi = $table.DataTable({
        data: isConsolidated ? buildConsolidatedData() : buildDetailedData(),
        responsive: true,
        pageLength: 50,
        lengthMenu: [[25, 50, 100, 250, -1], [25, 50, 100, 250, 'Todos']],
        order: [[0, 'asc']],
        language: { url: 'https://cdn.datatables.net/plug-ins/2.2.2/i18n/pt-BR.json' },
        buttons: [{
          extend: 'excelHtml5', text: 'Excel', title: 'pulse_ratings_consulta',
          exportOptions: { columns: isConsolidated ? [0,1,2,3,4,5,7,9] : [0,1,2,3,4,5,6,7,9] }
        }],
        dom: '<"dt-length-placeholder"l>t<"dt-info-placeholder"i><"dt-paginate-placeholder"p>',
        columns: buildColumns(isConsolidated),
      });

      setTimeout(moveDtControls, 100);
      applyFilters();
      bindRowClick();
    });
