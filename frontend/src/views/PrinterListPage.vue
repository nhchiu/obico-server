<template>
  <page-layout>
    <template #topBarRight>
      <div class="action-panel">
        <!-- Detective Hours -->
        <a
          v-if="isEnt"
          href="/user_preferences/dh/"
          class="btn shadow-none action-btn icon-btn hours-btn"
          :style="{ marginRight: `${String(dhBadgeNum).length * 0.25}rem` }"
          :title="dhBadgeNum + ' AI Detection Hours'"
        >
          <svg class="custom-svg-icon">
            <use href="#svg-detective-hours"></use>
          </svg>
          <span id="user-credits" class="badge badge-light">{{ dhBadgeNum }}</span>
          <span class="sr-only">AI Detection Hours</span>
        </a>
        <!-- Sorting -->
        <b-dropdown right no-caret toggle-class="action-btn icon-btn" title="Sort By">
          <template #button-content>
            <i class="fas fa-sort-amount-down"></i>
          </template>
          <sorting-dropdown
            :local-storage-prefix="sortingLocalStoragePrefix"
            :sorting-options="sortingOptions"
            :sorting-value="sortingValue"
            @onSortingUpdated="onSortingUpdated"
          />
        </b-dropdown>
        <!-- Filtering -->
        <b-dropdown
          right
          no-caret
          toggle-class="action-btn icon-btn"
          menu-class="scrollable"
          title="Filter"
        >
          <template #button-content>
            <i class="fas fa-filter"></i>
          </template>
          <filtering-dropdown
            :local-storage-prefix="filterLocalStoragePrefix"
            :filter-options="filterOptions"
            :filter-values="filterValues"
            @onFilterUpdated="onFilterUpdated"
          />
        </b-dropdown>
        <!-- Mobile Menu -->
        <b-dropdown right no-caret toggle-class="icon-btn d-md-none">
          <template #button-content>
            <i class="fas fa-ellipsis-v"></i>
          </template>
          <cascaded-dropdown ref="cascadedDropdown" :menu-options="mobileMenuOptions">
            <template #sorting>
              <sorting-dropdown
                :local-storage-prefix="sortingLocalStoragePrefix"
                :sorting-options="sortingOptions"
                :sorting-value="sortingValue"
                @onSortingUpdated="onSortingUpdated"
              />
            </template>
            <template #filtering>
              <filtering-dropdown
                :local-storage-prefix="filterLocalStoragePrefix"
                :filter-options="filterOptions"
                :filter-values="filterValues"
                @onFilterUpdated="onFilterUpdated"
              />
            </template>
          </cascaded-dropdown>
        </b-dropdown>
      </div>
    </template>

    <!-- Page content -->
    <template #content>
      <active-filter-notice :filter-values="filterValues" @onShowAllClicked="resetFilters" />

      <!-- Printers list -->
      <b-container class="printer-list-page">
        <b-row v-if="loading">
          <b-col class="text-center">
            <b-spinner class="my-5" label="Loading..."></b-spinner>
          </b-col>
        </b-row>
        <b-row v-if="visiblePrinters.length" class="printer-cards justify-content-center">
          <printer-card
            v-for="printer in visiblePrinters"
            :key="printer.id"
            :printer="printer"
            :is-pro-account="user.is_pro"
            class="printer-card-wrapper"
            @PrinterUpdated="onPrinterUpdated"
            @printModalOpened="() => (targetPrinter = printer)"
          ></printer-card>
        </b-row>
        <div class="row justify-content-center">
          <div id="new-printer" class="col-sm-12 col-lg-6">
            <div class="new-printer-container">
              <a href="/printers/wizard/">
                <svg class="icon">
                  <use href="#svg-add-printer"></use>
                </svg>
                <div>Link New Printer</div>
              </a>
            </div>
          </div>
        </div>
        <b-row v-show="shouldShowArchiveWarning" class="bottom-messages">
          <b-col>
            <div class="alert alert-warning alert-dismissible fade show mb-3" role="alert">
              <div class="warning">
                <div>
                  {{ archivedPrinterNum }} {{ 'printer' | pluralize(archivedPrinterNum) }} have been
                  archived.
                </div>
                <a href="/ent/printers/archived/" class="warning-action">Show Archived Printers</a>
              </div>
              <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
              </button>
            </div>
          </b-col>
        </b-row>
      </b-container>
      <b-modal id="b-modal-gcodes" size="lg" @hidden="resetGcodesModal">
        <g-code-file-page
          v-if="selectedGcodeId"
          :is-popup="true"
          :target-printer-id="targetPrinter.id"
          :route-params="{
            fileId: selectedGcodeId,
            printerId: selectedPrinterId,
          }"
          :on-close="() => $bvModal.hide('b-modal-gcodes')"
          @goBack="
            () => {
              selectedGcodeId = null
              scrollToTop()
            }
          "
        />
        <g-code-folders-page
          v-else
          :is-popup="true"
          :target-printer="targetPrinter"
          :route-params="{
            printerId: selectedPrinterId,
            parentFolder: null,
          }"
          :on-close="() => $bvModal.hide('b-modal-gcodes')"
          :saved-path="savedPath"
          scroll-container-id="b-modal-gcodes"
          @openFile="
            (fileId, printerId, path) => {
              selectedGcodeId = fileId
              selectedPrinterId = printerId
              savedPath = path
              scrollToTop()
            }
          "
        />
      </b-modal>
    </template>
  </page-layout>
</template>

<script>
import axios from 'axios'
import sortBy from 'lodash/sortBy'
import { setLocalPref } from '@src/lib/pref'
import { normalizedPrinter } from '@src/lib/normalizers'
import urls from '@config/server-urls'
import PrinterCard from '@src/components/printers/PrinterCard.vue'
import PageLayout from '@src/components/PageLayout.vue'
import CascadedDropdown from '@src/components/CascadedDropdown'
import SortingDropdown, { restoreSortingValue } from '@src/components/SortingDropdown'
import FilteringDropdown, { restoreFilterValues } from '@src/components/FilteringDropdown'
import { user, settings } from '@src/lib/page-context'
import GCodeFoldersPage from '@src/views/GCodeFoldersPage.vue'
import GCodeFilePage from '@src/views/GCodeFilePage.vue'
import ActiveFilterNotice from '@src/components/ActiveFilterNotice'

const SortingLocalStoragePrefix = 'printersSorting'
const SortingOptions = {
  options: [
    { title: 'Name', key: 'name' },
    { title: 'Created at', key: 'created_at' },
  ],
  default: { sorting: 'created_at', direction: 'desc' },
}

const FilterLocalStoragePrefix = 'printersFiltering'
const FilterOptions = {
  status: {
    title: 'Print Status',
    queryParam: 'status',
    values: [
      { key: 'none', title: 'All Printers' },
      { key: 'online', title: 'Online Printers' },
      { key: 'active', title: 'Active Printers' },
    ],
    default: 'none',
  },
}

export default {
  name: 'PrinterListPage',

  components: {
    PrinterCard,
    PageLayout,
    CascadedDropdown,
    SortingDropdown,
    FilteringDropdown,
    GCodeFoldersPage,
    GCodeFilePage,
    ActiveFilterNotice,
  },

  data: function () {
    return {
      user: null,
      printers: [],
      loading: true,
      isEnt: false,
      archivedPrinterNum: 0,

      // gcodes browse modal
      selectedGcodeId: null,
      selectedPrinterId: null,
      targetPrinter: null,
      savedPath: [null],

      // Sorting
      sortingLocalStoragePrefix: SortingLocalStoragePrefix,
      sortingOptions: SortingOptions,
      sortingValue: restoreSortingValue(SortingLocalStoragePrefix, SortingOptions),

      // Filtering
      filterLocalStoragePrefix: FilterLocalStoragePrefix,
      filterOptions: FilterOptions,
      filterValues: restoreFilterValues(FilterLocalStoragePrefix, FilterOptions),
    }
  },

  computed: {
    dhBadgeNum() {
      if (this.user && this.user.is_dh_unlimited) {
        return '\u221E'
      } else {
        return Math.round(this.user.dh_balance)
      }
    },
    mobileMenuOptions() {
      const options = [
        {
          key: 'sorting',
          icon: 'fas fa-sort-amount-down',
          title: `Sort`,
          expandable: true,
        },
        {
          key: 'filtering',
          icon: 'fas fa-filter',
          title: `Filter`,
          expandable: true,
        },
      ]

      if (this.isEnt) {
        options.unshift({
          key: 'dh',
          icon: 'fas fa-hourglass-half',
          title: `${this.dhBadgeNum} AI Detection Hours`,
          href: '/user_preferences/dh/',
        })
      }

      return options
    },

    visiblePrinters() {
      let printers = this.printers
      switch (this.filterValues.status) {
        case 'online':
          printers = printers.filter((p) => !p.isDisconnected())
          break
        case 'active':
          printers = printers.filter((p) => p.isActive())
          break
        case 'none':
          break
      }

      if (this.sortingValue.sorting.key === 'created_at') {
        printers = sortBy(printers, (p) => p.createdAt())
      } else if (this.sortingValue.sorting.key === 'name') {
        printers = sortBy(printers, (p) => p.name)
      }

      if (this.sortingValue.direction.key === 'desc') {
        printers.reverse()
      }

      return printers
    },
    hiddenPrinterCount() {
      return this.printers.length - this.visiblePrinters.length
    },
    shouldShowArchiveWarning() {
      return this.archivedPrinterNum > 0
    },
  },

  created() {
    const { IS_ENT } = settings()
    this.isEnt = !!IS_ENT
    this.user = user()
    this.fetchPrinters()
  },

  methods: {
    fetchPrinters() {
      this.loading = true
      return axios
        .get(urls.printers(), {
          params: {
            with_archived: true,
          },
        })
        .then((response) => {
          this.loading = false
          response.data.forEach((p) => {
            if (p.archived_at) {
              this.archivedPrinterNum += 1
            } else {
              this.insertPrinter(normalizedPrinter(p))
            }
          })
        })
    },
    insertPrinter(printer) {
      this.printers.push(printer)
    },
    onPrinterUpdated(printer) {
      let index = this.printers.findIndex((p) => p.id == printer.id)
      if (index < 0) {
        // FIXME any alert here?
        return
      }

      this.$set(this.printers, index, printer)
    },
    scrollToTop() {
      document.querySelector('#b-modal-gcodes').scrollTo(0, 0)
    },
    resetGcodesModal() {
      this.selectedGcodeId = null
      this.targetPrinter = null
    },

    // Sorting
    onSortingUpdated(sortingValue) {
      this.sortingValue = sortingValue
    },

    // Filtering
    onFilterUpdated(filterOptionKey, filterOptionValue) {
      this.filterValues[filterOptionKey] = filterOptionValue
    },
    resetFilters() {
      for (const key of Object.keys(this.filterValues)) {
        this.filterValues[key] = 'none'
        setLocalPref(`${FilterLocalStoragePrefix}-${key}`, 'none')
      }
    },
  },
}
</script>

<style lang="sass" scoped>
.printer-list-page
  .consider-upgrade
    margin-bottom: var(--gap-between-blocks)

  .printer-cards
     margin-top: calc(var(--gap-between-blocks) * -1)

  .printer-card-wrapper
    margin-top: var(--gap-between-blocks)

  .bottom-messages
    margin-top: var(--gap-between-blocks)

  .warning
    display: flex
    flex-direction: row
    flex-wrap: wrap
    justify-content: space-between
    align-items: center

    .warning-action
      padding: 0.25em 0
      font-weight: bolder
      font-size: 1.1em
      margin-left: auto

.btn.hours-btn
  position: relative
  color: var(--color-text-primary)

  .badge
    position: absolute
    left: 18px
    top: 4px
    border-radius: var(--border-radius-sm)
    background-color: var(--color-primary)
    height: auto
    font-size: .625rem

.custom-svg-icon
  height: 1.125rem
  width: 1.125rem

::v-deep .dropdown-item .clickable-area
  margin: -0.25rem -1.5rem
  padding: 0.25rem 1.5rem
</style>

<style lang="sass">
#b-modal-gcodes
  .modal-header
    display: none
  .modal-body
    padding: 0
  .modal-footer
    display: none
</style>
