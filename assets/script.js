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
      // Do not update if strain order reflects current heatmap strains axis
      if (JSON.stringify(ret) === JSON.stringify(data.heatmap_y_strains)) {
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
     * jQuery handler to keep watch as the user scrolls through the heatmap. A
     * new handler is attached everytime the heatmap nt pos axis figure is
     * generated.
     * Special precautions had to be taken due to the fact the heatmap nt pos
     * axis figure may be generated before it is inserted into the dom, so we
     * cannot rely on just parsing HTML from it on app launch.
     * @param _ Heatmap nt pos axis figure generated
     * @param {Object} data ``data_parser.get_data`` return value
     */
    makeHistogramRelPosBarDynamic: (_, data) => {
      const $heatmapCenterDiv = $('#heatmap-center-div')
      const tickValArr = data['heatmap_x_nt_pos']
      const heatmapCellsWidth = data['heatmap_cells_fig_width']
      const tickWidth = heatmapCellsWidth / tickValArr.length
      const lastHistogramBin =
          Math.ceil(parseInt(tickValArr[tickValArr.length-1]/100) * 100)

      // We do not want to accumulate handlers
      $heatmapCenterDiv.off('scroll.foo')
      // Add the handler that dynamically changes the `histogram-rel-pos-bar`
      // div as the user scrolls.
      $heatmapCenterDiv.on('scroll.foo', (e) => {
        // Bounds of visible heatmap, which does not include overflow
        const boundHeatmapWidth = e.currentTarget.getBoundingClientRect().width

        const numOfVisibleTicks = Math.floor((boundHeatmapWidth / tickWidth))

        // How far left the user has scrolled the heatmap
        let scrollLeft = $heatmapCenterDiv.scrollLeft()
        // We want to make scrollLeft === 0 at the beginning of the heatmap--
        // not the beginning of the left padding.
        scrollLeft -= parseInt($heatmapCenterDiv.css('padding-left'), 10)

        // Index of first visible tick in ``tickValArr``
        let leftMostVisibleTickIndex = Math.round(scrollLeft / tickWidth)
        // Due to left padding, could be below 0. Make 0 if so.
        leftMostVisibleTickIndex =
            leftMostVisibleTickIndex < 0 ? 0 : leftMostVisibleTickIndex
        // Index of last visible tick in ``tickValArr``
        const rightMostVisibleTickIndex =
            leftMostVisibleTickIndex + numOfVisibleTicks - 1

        const leftMostVisibleTick = tickValArr[leftMostVisibleTickIndex]
        const rightMostVisibleTick = tickValArr[rightMostVisibleTickIndex]

        // Calculate margins for `histogram-rel-pos-bar` as percents, and apply
        // them.
        const leftMarginPercent =
            leftMostVisibleTick/lastHistogramBin * 100
        const rightMarginPercent =
            (lastHistogramBin-rightMostVisibleTick)/lastHistogramBin * 100
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
    },
    /**
     * Using pure JS, link the scrolling of the heatmap cells and y-axis
     * containers.
     * Lifted from https://stackoverflow.com/a/41998497/11472358
     * Seems to work smoothly.
     * @param _ Heatmap strains-axis fig generated
     * @param __ Heatmap sample size axis fig generated
     * @param ___ Heatmap cells fig generated
     */
    linkHeatmapCellsYScrolling: (_, __, ___) => {
      let isSyncingLeftScroll = false;
      let isSyncingMidScroll = false;
      let isSyncingRightScroll = false;
      const leftDiv =
          document.getElementById('heatmap-strains-axis-inner-container');
      const midDiv = document.getElementById('heatmap-cells-inner-container');
      const rightDiv =
          document.getElementById('heatmap-sample-size-axis-inner-container');

      leftDiv.onscroll = function() {
        if (!isSyncingLeftScroll) {
          isSyncingMidScroll = true;
          midDiv.scrollTop = this.scrollTop;
          isSyncingRightScroll = true;
          rightDiv.scrollTop = this.scrollTop;
        }
        isSyncingLeftScroll = false;
      }

      midDiv.onscroll = function() {
        if (!isSyncingMidScroll) {
          isSyncingLeftScroll = true;
          leftDiv.scrollTop = this.scrollTop;
          isSyncingRightScroll = true;
          rightDiv.scrollTop = this.scrollTop;
        }
        isSyncingMidScroll = false;
      }

      rightDiv.onscroll = function() {
        if (!isSyncingRightScroll) {
          isSyncingLeftScroll = true;
          leftDiv.scrollTop = this.scrollTop;
          isSyncingMidScroll = true;
          midDiv.scrollTop = this.scrollTop;
        }
        isSyncingRightScroll = false;
      }
    }
  }
});
