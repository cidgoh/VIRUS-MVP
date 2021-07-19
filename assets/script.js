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
          checkboxDivs = e1.find(':checkbox')
        } else {
          checkboxDivs = e2.find(':checkbox')
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
    },
    /**
     * Add a jQuery handler that dynamically changes the size and position of
     * the `histogram-rel-pos-bar` div.
     * This is quite hackey, because Plotly does not offer any native features
     * to implement this feature. This function returns nothing, but attaches a
     * jQuery handler to keep watch as the user scrolls through the heatmap.
     * Several allowances had to be made, so you should read the comments in
     * the function below for further clarification, if needed.
     * Our inputs provide no relevant information, but we chose to use the data
     * dcc variable as an input because that is when the ticks in the heatmap
     * may change, and the jQuery handler needs to be replaced. The input
     * telling you the histogram and heatmap figures were rendered may prevent
     * race conditions, since we are venturing outside Plotly and Dash here.
     * @param _ Histogram figure rendered
     * @param __ Heatmap center figure rendered
     * @param ___ Data dcc variable changed
     */
    makeHistogramRelPosBarDynamic: (_, __, ___) => {
      // A list of all ticks in the heatmap, and a sneaky calculation that tells
      // you what the last histogram bin is going to be. Plotly does not give up
      // that information easily.
      const allTicks = $('#heatmap-nt-pos-axis-fig').find('.xtick>text')
      const lastHistogramBin =
          Math.ceil(parseInt(allTicks[allTicks.length-1].textContent)/100) * 100

      const $heatmapCenterDiv = $('#heatmap-center-div')
      // We do not want to accumulate handlers
      $heatmapCenterDiv.off('scroll.foo')
      // Add the handler that dynamically changes the `histogram-rel-pos-bar`
      // div as the user scrolls.
      $heatmapCenterDiv.on('scroll.foo', (e) => {
        // Bounds of visible heatmap, which does not include overflow
        const heatmapDivBounds = e.currentTarget.getBoundingClientRect()
        // Filter ticks that are not hidden by overflow
        const visibleTicks = allTicks.filter((_, el) => {
          const tickDivBounds = el.getBoundingClientRect()
          const tickDivCenter = tickDivBounds.left + tickDivBounds.width/2
          const tooFarLeft = tickDivCenter < heatmapDivBounds.left
          const tooFarRight = tickDivCenter > heatmapDivBounds.right
          return !(tooFarLeft || tooFarRight)
        })
        // The ticks are text elements, so we need to retrieve their content
        const leftBoundary =
            parseInt(visibleTicks[0].textContent)
        const rightBoundary =
            parseInt(visibleTicks[visibleTicks.length-1].textContent)
        // Calculate margins for `histogram-rel-pos-bar` as percents, and apply
        // them.
        const leftMarginPercent =
            leftBoundary/lastHistogramBin * 100
        const rightMarginPercent =
            (lastHistogramBin-rightBoundary)/lastHistogramBin * 100
        const margins = {
          'margin-left': `${leftMarginPercent}%`,
          'margin-right': `${rightMarginPercent}%`
        }
        $('#histogram-rel-pos-bar').css(margins)
      })
      // Last bits of hackeyness. We need to trigger a scroll event each time
      // this function is called, so the `histogram-rel-pos-bar` is at an
      // appropriate size to begin with. We also need to trigger it when the
      // window is resized, because the bootstrap containers are fluid. We
      // return null, because we have to return something.
      $heatmapCenterDiv.trigger('scroll')
      $(window).resize(() => {$heatmapCenterDiv.trigger('scroll')})
      return null
    }
  }
});
