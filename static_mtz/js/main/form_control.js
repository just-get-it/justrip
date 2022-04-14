function getSelectValues(query) {
  var groups = [];
  [...document.querySelector(query).options].map((x, i) => {
    if (x.selected === true) {
      groups.push(x.value);
    }
  });
return groups
}
function create_option(key) {
  return `<option value=${key}>${key}</option>`;
}
function create_options(set) {
  array = Array.from(set);
  console.log(array);
  let options = `<option value="" >-----</option>`;
  set.forEach((val) => {
    options += create_option(val);
  });
  return options;
}
window.onload = () => {
  document.getElementById("id_group").addEventListener("change", async (e) => {
    const selected_group = getSelectValues("#id_group")
    console.log("vehicle group changed to " + selected_group);
    vehical_types_data = await fetch(
      `${window.location.origin}/ajax_vehical_type_filter/${selected_group}`
    )
      .then((res) => res.json())
      .then((data) => data);
    console.log(vehical_types_data);
    let vehicle_types = new Set();

    vehical_types_data.map((data, index) => {
      vehicle_types.add(data.pk);
    });
    document.getElementById("id_type").innerHTML =
      create_options(vehicle_types);
  });
  document.getElementById("id_type").addEventListener("change", async (e) => {
    const selected_group = getSelectValues("#id_group")
    const selected_type = getSelectValues("#id_type")

    console.log("vehicle type changed to " + selected_type);
    vehical_companies_data = await fetch(
      `${window.location.origin}/ajax_vehical_company_filter/${selected_group}/${selected_type}`
    )
      .then((res) => res.json())
      .then((data) => data);
    // console.log(vehical_companies_data);
    let vehicle_types = new Set();

    vehical_companies_data.map((data, index) => {
      vehicle_types.add(data.pk);
    });
    document.getElementById("id_company").innerHTML =
      create_options(vehicle_types);
  });
};
