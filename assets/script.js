window.dash_clientside = Object.assign({}, window.dash_clientside, {
  clientside: {
    /**
     * Make the checkboxes in the select lineage modal draggable within their
     * respective form groups, using the JQuery UI sortable plugin.
     * @param {Array<Object>} idArray Dash pattern matching id values for
     *  checkboxes in select lineages modal.
     * @return {Boolean} ``true`` if we successfully made the checkboxes
     *  draggable.
     */
    makeSelectLineagesModalCheckboxesDraggable: (idArray) => {
      // This function responds to all changes in the select lineages modal
      // body. But the checkboxes disappear when the modal is closed, so we
      // should do nothing when that happens.
      if (!idArray.length) return false

      for (const id of idArray) {
        // There are two elements in each id, and we do not know which order
        // they will be rendered in the HTML. So we try both.
        const idStr1 = JSON.stringify(id, Object.keys(id).sort())
        const idStr2 = JSON.stringify(id, Object.keys(id).sort().reverse())
        // JQuery currently struggles with special characters, so use
        // ``document``.
        const e1 = $(document.getElementById(idStr1))
        const e2 = $(document.getElementById(idStr2))
        if (e1.length) {
          $(e1).sortable()
          $(e1).disableSelection()
        } else {
          $(e2).sortable()
          $(e2).disableSelection()
        }
      }
      return true
    },
    /**
     * Get the order of the strains in the select lineage modal after the user
     * clicks the OK button.
     * @param _ OK button in select lineages modal was clicked
     * @param {Array<Object>} idArray Dash pattern matching id values for
     *  checkboxes in select lineages modal.
     * @param {Object} data ``data_parser.get_data`` return value
     * @return {Array<string>} The strains corresponding the checkboxes in the
     *  select lineages modal, in the final order they were in when the OK
     *  button was clicked.
     */
    getStrainOrder: (_, idArray, data) => {
      let ret = []
      for (const id of idArray) {
        // There are two elements in each id, and we do not know which order
        // they will be rendered in the HTML. So we try both.
        const idStr1 = JSON.stringify(id)
        const idStr2 = JSON.stringify(id, Object.keys(id).sort())
        // JQuery currently struggles with special characters, so use
        // ``document``.
        const e1 = $(document.getElementById(idStr1))
        const e2 = $(document.getElementById(idStr2))
        let checkboxDivs;
        if (e1.length) {
          checkboxDivs = e1.find(":checkbox")
        } else {
          checkboxDivs = e2.find(":checkbox")
        }
        for (const checkboxDiv of checkboxDivs) {
          ret.push(checkboxDiv.value)
        }
      }
      // Heatmap displays rows in reverse
      ret = ret.reverse()
      // Do not update if strain order reflects current heatmap y axis
      if (JSON.stringify(ret) === JSON.stringify(data.heatmap_y)) {
        return window.dash_clientside.no_update
      } else {
        return ret
      }
    }
  }
});
