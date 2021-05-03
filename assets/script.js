window.dash_clientside = Object.assign({}, window.dash_clientside, {
  clientside: {
    /**
     * TODO
     * @param idArray
     * @return
     */
    makeDraggable: (idArray) => {
      if (!idArray.length) return false

      for (const id of idArray) {
        const idStr1 = JSON.stringify(id)
        const idStr2 = JSON.stringify(id, Object.keys(id).sort())
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
     * TODO
     */
    getDraggable: (_, idArray) => {
      const ret = []
      for (const id of idArray) {
        const idStr1 = JSON.stringify(id)
        const idStr2 = JSON.stringify(id, Object.keys(id).sort())
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
      return ret
    }
  }
});
